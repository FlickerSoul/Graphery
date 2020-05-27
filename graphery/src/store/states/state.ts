export interface RootState {
  drawer: boolean;
}

export interface MetaState {
  siteName: string;
  navigationButtons: { name: string; icon: string }[];
  siteLogo: string;
  headerSize: 66;
  footerHTML: string;
}

export const enum NotificationStatus {
  success = 'success',
  info = 'info',
  warning = 'warning',
  error = 'error',
  empty = '',
}

export interface NotificationState {
  status: NotificationStatus;
  message: string;
  details: string;
}

export interface Graph {
  id: string;
  name: string;
  cyjs: object | string;
  layoutEngine: GraphLayoutEngines;
  info: string;
}

export interface TutorialState {
  articleId: string | null;
  article: {
    title: string;
    content: string;
    authors: string[];
    categories: string[];
    time: string;
  } | null;
  graphIDs: string[] | null;
  // use v-for to spread graphs and make :key bind to id (or serial code?)
  graphs: Graph[] | null;
  codes: { [id: string]: { graphId: string; codes: string } } | null;
}

export const enum GraphLayoutEngines {
  dagre = 'dagre',
  hierarchical = 'hac',
}

export interface TutorialRequestState {
  articleId?: string;
  article?: {
    title: string;
    content: string;
    authors: string[];
    categories: string[];
    time: string;
  } | null;
  graphIDs?: string[] | null;
  // use v-for to spread graphs and make :key bind to id (or serial code?)
  graphs?: Graph[] | null;
  codes?: { [id: string]: { graphId: string; codes: string } } | null;
}

export interface SettingState {
  dark: boolean;
  // graph page
  graphSplitPos: number;
  graphDark: boolean;

  // graph render
  hideEdgeWhenRendering: boolean;
  renderViewportOnly: boolean;
  motionBlurEnabled: boolean;
  motionSensitivityLevel: number;

  // editor settings
  tabNum: number;
  softTab: boolean;
  fontSize: number;
  wrap: boolean;
}
