import {
  DateTimeMixinType,
  IDMixinType,
  IsPublishedMixinType,
} from '@/store/states/state';
import { ResultJsonTypeFromQueryData } from '@/store/modules/ResultJsonStorage/ResultJsonStoreState';

export interface CodeType extends IDMixinType {
  code?: string;
}

export interface CodeStoreType {
  codeObjectList: CodeType[] | null;
  currentCodeId: string | null;
  currentCodeObject: CodeType | null;
}

export interface CodeTypeFromQueryData
  extends CodeType,
    DateTimeMixinType,
    IsPublishedMixinType {
  tutorial?: object;
  execresultjsonSet?: ResultJsonTypeFromQueryData[];
}
