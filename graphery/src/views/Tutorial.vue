<template>
  <!-- TODO change list and app bar color -->
  <div style="overflow: hidden;">
    <q-splitter
      v-if="!onXsScreen"
      v-model="splitPos"
      :style="tutorialStyle"
      :horizontal="$q.screen.lt.md"
      :separator-class="
        $q.screen.lt.md
          ? 'resizable-h-separator-splitter'
          : 'resizable-v-separator-splitter'
      "
      class="overflow-hidden-splitter"
    >
      <!-- FIXME: using computed-->
      <template v-slot:before>
        <q-splitter
          id="graph-code-section"
          v-model="editorSplitPos"
          horizontal
          separator-class="resizable-h-separator-splitter zero-z-index-separator"
          class="overflow-visible-splitter"
        >
          <template v-slot:before>
            <CytoscapeWrapper
              ref="cytoscapeWrapper"
              id="cytoscape-wrapper"
              :selectLoadingOverride="execLoading"
              @cytoscapeInstanceLoaded.once="onCytoscapeInstanceLoaded"
              style="overflow-y: hidden;"
            ></CytoscapeWrapper>
          </template>
          <template v-slot:separator>
            <SplitterSeparator :horizontal="true" />
          </template>
          <template v-slot:after>
            <EditorControlUnit
              ref="editorControlUnit"
              :slider-length="editorControlSliderLength"
              :disable-override="execLoading"
              :execLoading="execLoading"
              @onSliderChange="onSliderChange"
              @onPushToCloudExec="onPushToCloudExec"
              @onPushToLocalExec="onPushToLocalExec"
              @onCopyCurrentCode="onCopyCurrentCode"
              @onPasteFromClipboard="onPasteFromClipboard"
              @onChangeVariableListOrientation="onChangeVariableListOrientation"
              @onCallWorkSpace="onCallWorkSpace"
            />
            <EditorWrapper
              v-show="currentTab === 'editor'"
              id="editor-wrapper"
              ref="editorWrapper"
              class="full-height"
              :editorLoadingOverride="execLoading"
              @editorContentChanged="onEditorContentChanged"
              @editorInstanceLoaded.once="onEditorInstanceLoaded"
              @clearHighlightFromVarList="clearHighlightsElementsFromVarList"
              @highlightFromVarList="highlightElementsFromVarList"
              @toggleHighlightFromVarList="toggleHighlightsFromVarList"
            ></EditorWrapper>
            <GraphInfo v-show="currentTab === 'graph-info'"></GraphInfo>
            <HowToHelper v-show="currentTab === 'how-to'"></HowToHelper>
            <!-- page sticky -->
          </template>
        </q-splitter>
      </template>
      <template v-slot:separator>
        <SplitterSeparator :horizontal="$q.screen.lt.md" />
      </template>
      <template v-slot:after>
        <EditorSectionPanelSwitchSticky @switchTabView="onSwitchTabView" />
        <TutorialArticle
          class="full-height"
          @breakpointClicked="onBreakpointClicked"
        ></TutorialArticle>
      </template>
    </q-splitter>
    <!-- view for small screen -->
    <TutorialArticle v-else></TutorialArticle>
    <MobileViewWarningPopup v-if="onXsScreen" />
  </div>
</template>

<script>
  import { headerSize } from '@/store/states/meta';
  import { mapState, mapActions } from 'vuex';
  import { apiCaller } from '@/services/apis';
  import {
    pullTutorialArticle,
    pullTutorialDetailQuery,
  } from '@/services/queries';
  import { errorDialog, successDialog } from '@/services/helpers';

  import GraphCodeBridge from '@/components/framework/GraphEditorControls/GraphCodeBridge';
  import TabSwitchMixin from '@/components/framework/EditorSectionSwitch/TabSwitchMixin';
  import OnXsScreenMixin from '@/components/mixins/OnXsScreenMixin';

  import TutorialArticle from '@/components/tutorial/TutorialArticle';
  import CytoscapeWrapper from '@/components/tutorial/CytoscapeWrapper';
  import EditorWrapper from '@/components/tutorial/EditorWrapper';
  import SplitterSeparator from '@/components/framework/SplitterSeparator';
  import EditorControlUnit from '@/components/framework/EditorControlUnit';
  import ProductGuideMixin from '@/components/mixins/ProductGuideMixin';

  export default {
    mixins: [
      GraphCodeBridge,
      TabSwitchMixin,
      OnXsScreenMixin,
      ProductGuideMixin,
    ],
    props: ['lang', 'url'],
    components: {
      SplitterSeparator,
      CytoscapeWrapper,
      TutorialArticle,
      EditorWrapper,
      EditorControlUnit,
      MobileViewWarningPopup: () =>
        import('@/components/framework/MobileViewWarningPopup'),
      EditorSectionPanelSwitchSticky: () =>
        import(
          '@/components/framework/EditorSectionSwitch/EditorSectionPanelSwitchSticky'
        ),
      GraphInfo: () => import('@/components/tutorial/GraphInfo.vue'),
      HowToHelper: () => import('@/components/tutorial/HowToHelper.vue'),
    },
    data() {
      return {
        editorSplitPos: 60,
      };
    },
    computed: {
      ...mapState('settings', ['graphSplitPos']),
      splitPos: {
        set(d) {
          this.$store.dispatch(
            'settings/changeGraphSplitPos',
            Math.round(d * 10) / 10
          );
        },
        get() {
          return this.graphSplitPos;
        },
      },
      tutorialStyle() {
        return {
          height: `calc(100vh - ${headerSize}px)`,
        };
      },
      currentLang() {
        return this.$i18n.locale;
      },
      showProductGuide() {
        return true;
      },
      shouldLoad() {
        return this.$store.getters['settings/showTutorialIntro'];
      },
    },
    methods: {
      ...mapActions('tutorials', ['clearAll', 'loadTutorial']),
      updateTutorialContent() {
        console.debug(
          'API calls to get details of the tutorial with url',
          this.url
        );
        apiCaller(pullTutorialDetailQuery, {
          url: this.url,
          translation: this.currentLang,
        })
          .then((data) => {
            if (!data) {
              throw Error('Invalid data returned.');
            }

            // TODO temporary fix
            if (data.tutorial.content === null) {
              this.$router.push({ name: '404' });
              return;
            }

            this.loadTutorial(data.tutorial);

            // NEW API
            // load current code id
            this.currentCodeId = data.tutorial.code.id;
            // since code is a single object
            this.loadCodeObjectListFromMatched([data.tutorial.code]);

            // load graph set directly
            this.loadGraphObjectListFromMatched(data.tutorial.graphSet);

            this.loadResultJsonListFromQueryData(
              data.tutorial.code.execresultjsonSet.map((obj) => ({
                ...obj,
                code: { id: data.tutorial.code.id },
              }))
            );
            // takes in two list
            this.initResultJsonPositions(
              data.tutorial.graphSet.map((obj) => obj.id),
              [data.tutorial.code.id]
            );
          })
          .catch((err) => {
            errorDialog({
              message: 'An error occurs during pulling tutorials. ' + err,
            });
          });
      },
      onBreakpointClicked(position) {
        if (this.onXsScreen) {
          errorDialog({
            message: 'The action is not supported on small-screen device',
          });
        }

        successDialog({
          message: `breakpoint ${position} clicked`,
        });
      },
      onBeforeExitCallback() {
        if (
          confirm(
            this.$i18n.t('product guide.before exit') +
              '\n' +
              this.$i18n.t('product guide.open again')
          )
        ) {
          this.$store.commit('settings/CHANGE_TUTORIAL_INTRO', false);
          return true;
        } else {
          return false;
        }
      },
    },
    watch: {
      currentLang: function(newVal) {
        this.$router.replace({
          name: 'Tutorial',
          params: {
            lang: newVal,
            url: this.$route.params.url,
          },
        });

        this.$store.commit('tutorials/CLEAR_ARTICLE_CONTENT');
        this.$store.commit('tutorials/CLEAR_AUTHOR_META_STATE');

        apiCaller(pullTutorialArticle, {
          url: this.url,
          translation: newVal,
        })
          .then((data) => {
            if (!data || !('tutorial' in data)) {
              throw Error('Invalid data returned.');
            }
            if (data.tutorial.content === null) {
              this.$store.commit('tutorials/LOAD_ARTICLE_CONTENT', '');
              throw Error('No Such Translation');
            }
            this.$store.commit(
              'tutorials/UPDATE_AUTHOR_META_DATA',
              data.tutorial.content.authors
            );
            this.$store.commit(
              'tutorials/LOAD_ARTICLE_CONTENT',
              data.tutorial.content
            );
          })
          .catch((err) => {
            errorDialog({
              message: `An error occurs during switching languages. ${err}`,
            });
          });
      },
    },
    created() {
      this.$i18n.locale = this.lang;
    },
    mounted() {
      if (!this.onXsScreen) {
        this.$q.notify({
          multiLine: true,
          message: this.$t('notify.editorEntry'),
          icon: 'mdi-code-json',
          timeout: 1500,
        });
      }

      // pull tutorials
      this.updateTutorialContent();

      // load intro guide
      this.loadIntroModule().then(() => {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const m = require('../components/mixins/ProductGuideSteps');
        this.addIntroSteps(
          m.startTutorialIntro.concat(
            m.tutorialUIProductGuide,
            m.graphUIProductGuide,
            m.editorProductGuide,
            m.controlUnitProductGuide
          )
        );
        this.startIntro();
      });
      // this.addIntroSteps(tutorialUIProductGuide);
    },
    destroyed() {
      this.clearAll();
    },
  };
</script>

<style lang="sass">
  .zero-z-index-separator
    z-index: 0
  .overflow-visible-splitter > .q-splitter__after
    overflow: visible
  .overflow-hidden-splitter > .q-splitter__before
    overflow: hidden
</style>
