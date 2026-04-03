/**
 * UI 文案常量 - 单一真相源
 * 所有页面和测试必须引用此处定义的文案
 */
export const UI_TEXT = {
  // 首页
  WELCOME_TITLE: '欢迎使用家庭检查单管理',
  WELCOME_DESC: '记录家人健康足迹，从添加第一位成员开始。',
  ADD_FIRST_MEMBER: '添加第一位成员',
  ADD_MEMBER: '添加家庭成员',
  
  // 成员表单
  FORM_TITLE_CREATE: '添加新成员',
  FORM_TITLE_EDIT: '修改成员档案',
  FORM_SUBMIT_CREATE: '保存并开始记录',
  FORM_SUBMIT_EDIT: '更新信息',
  FORM_DELETE: '删除此成员',
  
  // 字段标签
  LABEL_NAME: '姓名',
  LABEL_GENDER: '性别',
  LABEL_DOB: '出生年月',
  LABEL_TYPE: '成员类型',
  PLACEHOLDER_NAME: '请输入姓名',
  
  // 审核页
  REVIEW_TITLE: 'OCR 识别结果审核',
  
  // 错误状态
  ERROR_TITLE: '服务连接异常',
  ERROR_RETRY: '重试连接',
  
  // 成员类型
  MEMBER_TYPE_CHILD: '儿童',
  MEMBER_TYPE_ADULT: '成人',
  MEMBER_TYPE_SENIOR: '老人',
  
  // 状态
  NO_RECORDS: '尚无记录',
  LOADING: '加载中...',

  // 手动录入与 CRUD
  ACTION_MANUAL_ENTRY: '手动录入',
  ACTION_PHOTO_IDENTIFY: '拍照识别',
  ACTION_ADD_EXAM: '录入新检查单',
  ACTION_DELETE_RECORD: '删除记录',
  CONFIRM_DELETE_RECORD: '确定要删除这条检查记录及其所有指标吗？',
  LABEL_EXAM_DATE: '检查日期',
  LABEL_INSTITUTION: '检查机构',
  LABEL_OBSERVATIONS: '检查项',
  BTN_ADD_METRIC: '添加指标项',
  MSG_SAVE_SUCCESS: '保存成功',
  MSG_DELETE_SUCCESS: '删除成功',
  MSG_UPDATE_SUCCESS: '更新成功',
  MSG_SANITY_ERROR: '超出常规合理范围',

  // 趋势与历史
  LABEL_HISTORICAL_LIST: '历史记录清单',
  LABEL_LEFT_EYE: '左眼指标',
  LABEL_RIGHT_EYE: '右眼指标',
  LABEL_VALUE: '指标数值',
  LABEL_CURRENT: '当前',
  LABEL_PREVIOUS: '上次',
  LABEL_LIMIT_RANGE: '参考区间',
  LABEL_ALERT_TITLE: '异常提醒',
  ACTION_EDIT_VALUE: '修改数值',
} as const;
