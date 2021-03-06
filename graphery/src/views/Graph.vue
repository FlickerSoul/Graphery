<template>
  <div style="overflow: hidden; ">
    <q-splitter
      v-model="splitPos"
      :style="splitterStyle"
      :horizontal="verticalSplitter"
      :separator-class="
        verticalSplitter
          ? 'resizable-h-separator-splitter'
          : 'resizable-v-separator-splitter'
      "
      class="after-splitter-overflow-hidden"
    >
      <template v-slot:before>
        <CytoscapeWrapper
          ref="cytoscapeWrapper"
          :selectLoadingOverride="execLoading"
          @cytoscapeInstanceLoaded.once="onCytoscapeInstanceLoaded"
        ></CytoscapeWrapper>
      </template>
      <template v-slot:separator>
        <SplitterSeparator :horizontal="verticalSplitter" />
      </template>
      <template v-slot:after>
        <div id="editor-section">
          <q-bar class="graph-menu-bar">
            <div class="graph-menu-wrapper">
              <q-select
                class="graph-selector"
                :options="codeOptions"
                v-model="codeChoice"
                label="Code"
                :multiple="false"
                dropdown-icon="mdi-menu-down"
                :loading="codeObjectListEmpty"
                emit-value
                option-label="label"
                option-value="value"
                map-options
              >
                <template v-slot:no-option>
                  <q-item>
                    <q-item-section class="text-grey">
                      {{ $t('graph.No Result') }}
                    </q-item-section>
                  </q-item>
                </template>
                <template v-slot:prepend>
                  <q-icon name="code"></q-icon>
                </template>
              </q-select>
            </div>
            <div id="graph-info-toggle" class="q-ml-md">
              <q-btn
                dense
                outline
                size="md"
                icon="mdi-book-information-variant"
                @click="graphInfoPopupShow = true"
              ></q-btn>
              <SwitchTooltip :text="$t('graph.Show Graph Info')" />
            </div>
          </q-bar>
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
            ref="editorWrapper"
            style="max-height: calc(100% - 56px);"
            :editorLoadingOverride="execLoading"
            @editorContentChanged="onEditorContentChanged"
            @editorInstanceLoaded.once="onEditorInstanceLoaded"
            @clearHighlightFromVarList="clearHighlightsElementsFromVarList"
            @highlightFromVarList="highlightElementsFromVarList"
            @toggleHighlightFromVarList="toggleHighlightsFromVarList"
          ></EditorWrapper>
        </div>
      </template>
    </q-splitter>
    <MobileViewWarningPopup v-if="onXsScreen" />
    <GraphInfoPopup
      :dialog-model="graphInfoPopupShow"
      @dialogModelChange="
        (val) => {
          this.graphInfoPopupShow = val;
        }
      "
      :graph-abstract-markdown="graphInfoMarkdown"
    />
  </div>
</template>

<script>
  import { mapGetters, mapState } from 'vuex';
  import { headerSize } from '@/store/states/meta';
  import { apiCaller } from '@/services/apis';
  import { pullGraphAndCodeQuery } from '@/services/queries';
  import { errorDialog, warningDialog } from '@/services/helpers';
  import { emptyCodeTemplate, newModelUUID } from '@/services/params';

  import GraphCodeBridge from '@/components/framework/GraphEditorControls/GraphCodeBridge';
  import OnXsScreenMixin from '@/components/mixins/OnXsScreenMixin';
  import ProductGuideMixin from '../components/mixins/ProductGuideMixin';

  import EditorWrapper from '@/components/tutorial/EditorWrapper';
  import CytoscapeWrapper from '@/components/tutorial/CytoscapeWrapper';
  import SplitterSeparator from '@/components/framework/SplitterSeparator';
  import EditorControlUnit from '@/components/framework/EditorControlUnit';
  import { successDialog } from '../services/helpers';

  const defaultCodeOption = [
    {
      label: 'Default Empty Template',
      value: newModelUUID,
    },
  ];

  const defaultCodeSnippetList = [
    {
      name: '',
      id: newModelUUID,
      code: emptyCodeTemplate,
    },
  ];

  export default {
    mixins: [GraphCodeBridge, OnXsScreenMixin, ProductGuideMixin],
    props: ['lang', 'url'],
    metaInfo() {
      const graphTitle = this.headerTitle;
      return { title: graphTitle };
    },
    components: {
      SwitchTooltip: () => import('@/components/framework/SwitchTooltip'),
      GraphInfoPopup: () => import('@/components/framework/GraphInfoPopup'),
      EditorWrapper,
      CytoscapeWrapper,
      SplitterSeparator,
      MobileViewWarningPopup: () =>
        import('@/components/framework/MobileViewWarningPopup'),
      EditorControlUnit,
    },
    data() {
      return {
        codeOptions: defaultCodeOption,
        graphInfoPopupShow_: false,
      };
    },
    computed: {
      ...mapState('settings', ['graphSplitPos']),
      ...mapGetters('graphs', ['getCurrentGraphObjectTitle']),
      ...mapGetters('code', [
        'getCurrentCodeObject',
        'getCurrentCodeId',
        'codeObjectListEmpty',
      ]),
      graphInfoPopupShow: {
        set(d) {
          this.graphInfoPopupShow_ = d;
        },
        get() {
          return this.graphInfoPopupShow_;
        },
      },
      graphInfoMarkdown() {
        return this.currentGraphObject
          ? this.currentGraphObject['content']['abstract']
          : '';
      },
      headerTitle() {
        return this.getCurrentGraphObjectTitle
          ? this.getCurrentGraphObjectTitle
          : this.$t('nav.Graph');
      },
      codeChoice: {
        set(d) {
          this.$store.commit('code/LOAD_CURRENT_CODE_ID', d);
        },
        get() {
          return this.getCurrentCodeId;
        },
      },
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
      splitterStyle() {
        return {
          height: `calc(100vh - ${headerSize}px)`,
        };
      },
      requestPayload() {
        return {
          url: this.url,
        };
      },
      verticalSplitter() {
        return this.$q.screen.lt.md;
      },
      shouldLoad() {
        return this.$store.getters['settings/showGraphIntro'];
      },
    },
    methods: {
      flipGraphInfoDialog() {
        this.graphInfoPopupShow = !this.graphInfoPopupShow;
      },
      showGraphInfoDialog() {
        if (
          this.$store.getters['settings/graphAbstractPopupShow'] &&
          !this.onXsScreen
        ) {
          this.graphInfoPopupShow = true;
        }
      },
      generateDefaultJsonResults(graphId) {
        return [
          {
            json: '[]',
            graphId,
            codeId: newModelUUID,
          },
        ];
      },
      loadGraphAndCode() {
        apiCaller(pullGraphAndCodeQuery, this.requestPayload)
          .then((data) => {
            if (!data || !('graph' in data)) {
              throw Error('Invalid data returned');
            }

            const graphObj = data.graph;

            // the object is singular
            this.$store.commit('graphs/LOAD_GRAPH_OBJECT_LIST', [graphObj]);

            this.codeOptions = defaultCodeOption;
            const resultJsonList = this.generateDefaultJsonResults(graphObj.id);
            const codeObjectList = defaultCodeSnippetList;

            if (graphObj.execresultjsonSet.length > 0) {
              graphObj.execresultjsonSet.forEach((obj) => {
                this.codeOptions.unshift({
                  label: obj.code.name,
                  value: obj.code.id,
                });

                resultJsonList.push({
                  json: obj.json,
                  graphId: graphObj.id,
                  codeId: obj.code.id,
                });

                codeObjectList.unshift({
                  name: obj.code.name,
                  id: obj.code.id,
                  code: obj.code.code,
                });
              });
            } else {
              warningDialog({
                message: 'This graph has no code associated with it!',
              });
            }

            // Code Store
            this.$store.commit('code/LOAD_CODE_LIST', codeObjectList);
            this.$store.commit(
              'code/LOAD_CURRENT_CODE_ID',
              this.codeOptions[0].value
            );

            // JSON store
            this.initResultJsonPositions(
              [graphObj.id],
              codeObjectList.map((obj) => obj.id)
            );

            this.$store.commit(
              'rj/LOAD_RESULT_JSON_STRING_LIST',
              resultJsonList
            );

            this.$store.commit(
              'rj/LOAD_RESULT_JSON_OBJECT_LIST',
              resultJsonList.map((obj) => ({
                jsonObject: JSON.parse(obj.json),
                graphId: obj.graphId,
                codeId: obj.codeId,
              }))
            );

            if (this.introInstance === null) {
              this.showGraphInfoDialog();
            }
          })
          .catch((err) => {
            errorDialog({
              message: `An error occurs during fetching graph and code. ${err}`,
            });
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
          this.$store.commit('settings/CHANGE_GRAPH_INTRO', false);
          return true;
        } else {
          return false;
        }
      },
      onExitCallback() {
        this.showGraphInfoDialog();
      },
    },
    created() {
      this.$i18n.locale = this.lang;
    },
    mounted() {
      this.loadGraphAndCode();

      // load intro module
      this.loadIntroModule().then(() => {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const m = require('../components/mixins/ProductGuideSteps');

        this.addIntroSteps(
          m.startGraphIntro.concat(
            m.graphUIProductGuide,
            m.editorProductGuide,
            m.controlUnitProductGuide
          )
        );
        this.startIntro();
      });
    },
  };
</script>

<style lang="sass">
  .after-splitter-overflow-hidden > .q-splitter__after
    overflow: hidden
</style>
