<template>
  <q-table
    :data="tableContent"
    :columns="columns"
    :pagination="pagination"
    row-key="name"
    grid
    hide-header
    :loading="loadingContent"
  >
    <template v-slot:top>
      <AddNewButton
        :create-func="
          () => {
            $emit('startUpload');
          }
        "
      />
      <RefreshButton :fetch-func="fetchUploadsContent" />
    </template>
    <template v-slot:item="props">
      <div class="q-pa-xs col-xs-12 col-sm-4 col-md-3 col-lg-2">
        <UploadDisplayCard
          :displayInfo="{ url: props.row.relativeUrl, id: props.row.id }"
          :alias="props.row.alias"
          @showUploadInfo="(obj) => $emit('showUploadInfo', obj)"
        />
      </div>
    </template>
  </q-table>
</template>

<script>
  import loadingMixin from '../../mixins/LoadingMixin';
  import { apiCaller } from '@/services/apis';
  import { fetchUploads } from '@/services/queries';
  import { errorDialog } from '@/services/helpers';

  export default {
    mixins: [loadingMixin],
    components: {
      RefreshButton: () =>
        import('@/components/ControlPanel/parts/buttons/RefreshButton'),
      AddNewButton: () =>
        import('@/components/ControlPanel/parts/buttons/AddNewButton'),
      UploadDisplayCard: () =>
        import('@/components/ControlPanel/parts/cards/UploadDisplayCard'),
    },
    data() {
      return {
        columns: [
          {
            name: 'relativeUrl',
            label: 'relativeUrl',
            field: 'relativeUrl',
          },
          {
            name: 'alias',
            label: 'Alias',
            field: 'alias',
          },
          {
            name: 'id',
            label: 'id',
            field: 'id',
            required: true,
          },
        ],
        pagination: {
          sortBy: '',
          rowsPerPage: 20,
        },
        tableContent: [],
      };
    },
    methods: {
      fetchUploadsContent() {
        this.startLoading();
        apiCaller(fetchUploads)
          .then((data) => {
            if (!data || !('allUploads' in data)) {
              throw Error('Invalid data returned.');
            }

            this.tableContent = data.allUploads;
          })
          .catch((err) => {
            errorDialog({
              message: `An error occurs during fetching uploads. ${err}`,
            });
          })
          .finally(() => {
            this.finishedLoading();
          });
      },
    },
    mounted() {
      this.fetchUploadsContent();
    },
  };
</script>
