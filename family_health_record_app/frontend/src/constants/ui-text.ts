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
} as const;
