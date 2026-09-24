export const mockProjects = [
  {
    id: 'prj-001',
    name: 'Customer Portal',
    type: 'Full application',
    language: 'Python',
    framework: 'Flask',
    version: '1.4.2',
    branch: 'main',
    status: 'Demo analysis ready',
    findings: 3,
    lastScan: '16 Sep 2026 · 02:18',
    demo: true,
  },
];

export const mockAnalysisOptions = {
  scopes: [
    { id: 'file', label: 'Code file', accept: '.py,.js,.jsx' },
    { id: 'project', label: 'Full project', accept: '.zip' },
  ],
  scanProfiles: [
    { id: 'quick', label: 'Quick', description: 'Focused preview profile.' },
    { id: 'standard', label: 'Standard', description: 'Balanced coverage profile.' },
    { id: 'deep', label: 'Deep', description: 'Expanded code and standards coverage.' },
  ],
  standardsPacks: [
    { id: 'core-web', label: 'CWE + OWASP Top 10 + ASVS' },
    { id: 'cwe', label: 'CWE focused' },
  ],
  filterSchemaSource: 'BACKEND_CONTRACT_REQUIRED',
};

export const projectPassport = {
  id: 'prj-001',
  name: 'Customer Portal',
  version: '1.4.2',
  branch: 'main',
  analysisId: 'SC-2026-00104',
  createdAt: '14 Sep 2026',
  lastScan: '16 Sep 2026 · 02:18',
  language: 'Python 3.12',
  framework: 'Flask 3.x',
  projectType: 'Web application',
  scannerPack: 'Raqeeb SecureCode Pack 1.0',
  standards: 'CWE · OWASP Top 10 · ASVS',
  aiEngine: 'Configured code-reasoning model',
  aiUsage: 'AI-assisted in 3 of 7 workflow gates',
  aiDefinition: 'AI assists explanation, correlation, and candidate fixes. Closure is evidence-based.',
  scanMode: 'Deep',
  evidenceState: 'Partial',
  coverage: '96%',
};

export const workflowStages = [
  { id: 'fingerprint', label: 'Fingerprint', labelAr: 'البصمة التقنية' },
  { id: 'understand', label: 'Understand', labelAr: 'فهم الكود' },
  { id: 'scan', label: 'Scan', labelAr: 'الفحص' },
  { id: 'investigate', label: 'Investigate', labelAr: 'التحقيق' },
  { id: 'transform', label: 'Transform', labelAr: 'الإصلاح' },
  { id: 'verify', label: 'Verify', labelAr: 'التحقق' },
  { id: 'report', label: 'Report', labelAr: 'التقرير' },
];

export const mockTechnologyProfile = {
  language: 'Python 3.12',
  framework: 'Flask 3.x',
  database: 'PostgreSQL',
  architecture: 'Layered web application',
  files: 42,
  functions: 118,
  routes: 17,
  dependencies: 37,
  entryPoints: ['app/__init__.py', 'app/routes/users.py'],
  sensitiveAreas: ['Authentication', 'Authorization', 'Configuration', 'Database access'],
};

export const mockScanSummary = {
  profile: 'Deep',
  coverage: '96%',
  filesCovered: '40 / 42',
  functionsCovered: '113 / 118',
  rulesExecuted: 186,
  rulesPassed: 183,
  rulesFailed: 3,
  standards: ['CWE', 'OWASP Top 10', 'OWASP ASVS'],
  filtersSource: 'Backend-driven contract required',
  timeline: [
    'Language and framework profile prepared',
    'Source files indexed',
    'Security rules executed',
    'Findings correlated to functions',
    'Evidence candidates prepared',
  ],
};

export const mockWorkspaceFiles = [
  {
    id: 'users-route',
    name: 'users.py',
    path: 'app/routes/users.py',
    status: 'critical',
    purpose: 'Exposes user profile endpoints and delegates access decisions to services.',
    purposeAr: 'يعرض نقاط الوصول الخاصة بملفات المستخدمين ويمرر قرارات الوصول إلى طبقة الخدمات.',
    language: 'Python',
    findings: ['SC-001'],
    functions: [
      {
        name: 'get_user',
        line: 10,
        status: 'critical',
        purpose: 'Returns a user profile by identifier for an authenticated request.',
        purposeAr: 'يعيد ملف مستخدم اعتمادًا على المعرّف ضمن طلب تمت مصادقته.',
      },
      {
        name: 'list_users',
        line: 16,
        status: 'safe',
        purpose: 'Returns a paginated user list using a restricted service method.',
        purposeAr: 'يعيد قائمة مستخدمين مقسّمة إلى صفحات من خلال خدمة مقيّدة.',
      },
    ],
    code: `from flask import Blueprint, jsonify\nfrom app.auth import login_required\nfrom app.services.user_service import UserService\n\nusers = Blueprint("users", __name__)\nservice = UserService()\n\n@users.get("/api/users/<int:user_id>")\n@login_required\ndef get_user(user_id):\n    user = service.get_user(user_id)\n    return jsonify(user.to_dict())\n\n@users.get("/api/users")\n@login_required\ndef list_users():\n    return jsonify(service.list_visible_users())`,
  },
  {
    id: 'user-service',
    name: 'user_service.py',
    path: 'app/services/user_service.py',
    status: 'warning',
    purpose: 'Coordinates profile retrieval and account updates between routes and repositories.',
    purposeAr: 'ينسّق قراءة ملفات المستخدمين وتحديث الحساب بين المسارات وطبقة المستودعات.',
    language: 'Python',
    findings: ['SC-002'],
    functions: [
      {
        name: 'get_user',
        line: 8,
        status: 'warning',
        purpose: 'Retrieves a user record from the repository.',
        purposeAr: 'يسترجع سجل المستخدم من طبقة المستودع.',
      },
      {
        name: 'update_profile',
        line: 11,
        status: 'safe',
        purpose: 'Updates whitelisted profile fields after validation.',
        purposeAr: 'يحدّث حقول الملف المسموح بها بعد التحقق منها.',
      },
    ],
    code: `from app.repositories.user_repository import UserRepository\nfrom app.validators import validate_profile\n\nclass UserService:\n    def __init__(self):\n        self.repo = UserRepository()\n\n    def get_user(self, user_id):\n        return self.repo.get_by_id(user_id)\n\n    def update_profile(self, user_id, payload):\n        clean = validate_profile(payload)\n        return self.repo.update(user_id, clean)`,
  },
  {
    id: 'config',
    name: 'config.py',
    path: 'config.py',
    status: 'warning',
    purpose: 'Defines application configuration and environment-dependent defaults.',
    purposeAr: 'يعرّف إعدادات التطبيق والقيم التي تعتمد على بيئة التشغيل.',
    language: 'Python',
    findings: ['SC-003'],
    functions: [],
    code: `import os\n\nclass Config:\n    DEBUG = False\n    SECRET_KEY = "DEMO_PLACEHOLDER_VALUE"\n    DATABASE_URL = os.getenv("DATABASE_URL")`,
  },
  {
    id: 'validators',
    name: 'validators.py',
    path: 'app/validators.py',
    status: 'safe',
    purpose: 'Validates and normalizes user-controlled profile fields.',
    purposeAr: 'يتحقق من حقول الملف الشخصي القادمة من المستخدم ويطبّع قيمها.',
    language: 'Python',
    findings: [],
    functions: [
      {
        name: 'validate_profile',
        line: 4,
        status: 'safe',
        purpose: 'Restricts accepted profile fields and normalizes values.',
        purposeAr: 'يقيّد الحقول المقبولة ويطبّع القيم قبل استخدامها.',
      },
    ],
    code: `ALLOWED_FIELDS = {"display_name", "timezone"}\n\ndef validate_profile(payload):\n    return {\n        key: str(value).strip()\n        for key, value in payload.items()\n        if key in ALLOWED_FIELDS\n    }`,
  },
];

export const mockFindings = [
  {
    id: 'SC-001',
    fileId: 'users-route',
    function: 'get_user',
    line: 11,
    title: 'Missing object-level authorization',
    titleAr: 'غياب التحقق من صلاحية الوصول إلى الكائن',
    severity: 'Critical',
    cwe: 'CWE-639',
    standard: 'OWASP API Security · Object-level authorization',
    source: 'GET /api/users/<user_id>',
    sink: 'service.get_user(user_id)',
    trace: [
      'HTTP user_id',
      'routes.users.get_user()',
      'UserService.get_user()',
      'UserRepository.get_by_id()',
    ],
    rootCause: 'Authentication is enforced, but resource ownership is not checked.',
    rootCauseAr: 'المصادقة موجودة، لكن ملكية المورد لا يتم التحقق منها قبل إرجاع البيانات.',
    exploitability: 'Verified in isolated test workspace',
    exploitabilityAr: 'تم التحقق منها في بيئة اختبار معزولة',
    evidence: 'A signed-in test user could request a different user record by identifier.',
    evidenceAr: 'تمكن مستخدم اختبار مسجل الدخول من طلب سجل مستخدم آخر عبر المعرّف.',
    weakCode: `@login_required\ndef get_user(user_id):\n    user = service.get_user(user_id)\n    return jsonify(user.to_dict())`,
    secureCode: `@login_required\ndef get_user(user_id):\n    user = service.get_user_for_principal(\n        user_id=user_id,\n        principal_id=current_user.id,\n    )\n    return jsonify(user.to_dict())`,
    changedLines: '4 lines',
    originalFileName: 'users.py',
    language: 'Python',
    updateAction: 'object_authorization_fix',
    modification: 'Security Fix',
    modificationAr: 'إصلاح أمني',
    updatedFileContent: `from flask import Blueprint, jsonify
from flask_login import current_user
from app.auth import login_required
from app.services.user_service import UserService

users = Blueprint("users", __name__)
service = UserService()

@users.get("/api/users/<int:user_id>")
@login_required
def get_user(user_id):
    user = service.get_user_for_principal(
        user_id=user_id,
        principal_id=current_user.id,
    )
    return jsonify(user.to_dict())

@users.get("/api/users")
@login_required
def list_users():
    return jsonify(service.list_visible_users())`,
    verification: {
      functional: 'Pass',
      replay: 'Previous cross-account request is denied',
      rescan: 'Original finding not reproduced',
      retrace: 'Ownership control appears before resource return',
      closure: 'Verified remediated',
    },
  },
  {
    id: 'SC-002',
    fileId: 'user-service',
    function: 'get_user',
    line: 8,
    title: 'Authorization decision missing from service boundary',
    titleAr: 'قرار الصلاحية مفقود عند حدّ الخدمة',
    severity: 'High',
    cwe: 'CWE-862',
    standard: 'CWE · Missing Authorization',
    source: 'Authenticated request context',
    sink: 'Repository record return',
    trace: ['Route', 'UserService.get_user()', 'Repository'],
    rootCause: 'Service method has no principal context and cannot enforce ownership.',
    rootCauseAr: 'الدالة لا تستقبل سياق المستخدم الحالي، لذلك لا تستطيع فرض ملكية المورد.',
    exploitability: 'Reachable · verification required',
    exploitabilityAr: 'المسار قابل للوصول ويحتاج تحققًا',
    evidence: 'Static trace confirms a reachable authorization gap.',
    evidenceAr: 'التتبع الثابت يؤكد وجود فجوة صلاحيات قابلة للوصول.',
    weakCode: `def get_user(self, user_id):\n    return self.repo.get_by_id(user_id)`,
    secureCode: `def get_user_for_principal(self, user_id, principal_id):\n    user = self.repo.get_by_id(user_id)\n    if user.id != principal_id:\n        raise Forbidden()\n    return user`,
    changedLines: '5 lines',
    originalFileName: 'user_service.py',
    language: 'Python',
    updateAction: 'authorization_fix',
    modification: 'Security Fix',
    modificationAr: 'إصلاح أمني',
    updatedFileContent: `from werkzeug.exceptions import Forbidden
from app.repositories.user_repository import UserRepository
from app.validators import validate_profile

class UserService:
    def __init__(self):
        self.repo = UserRepository()

    def get_user_for_principal(self, user_id, principal_id):
        user = self.repo.get_by_id(user_id)
        if user.id != principal_id:
            raise Forbidden()
        return user

    def update_profile(self, user_id, payload):
        clean = validate_profile(payload)
        return self.repo.update(user_id, clean)`,
    verification: {
      functional: 'Pending',
      replay: 'Pending',
      rescan: 'Pending',
      retrace: 'Pending',
      closure: 'Candidate fix',
    },
  },
  {
    id: 'SC-003',
    fileId: 'config',
    function: null,
    line: 5,
    title: 'Hardcoded application secret',
    titleAr: 'سر تطبيقي مكتوب مباشرة داخل الكود',
    severity: 'High',
    cwe: 'CWE-798',
    standard: 'CWE · Use of Hard-coded Credentials',
    source: 'Source file',
    sink: 'SECRET_KEY',
    trace: ['config.py', 'Config.SECRET_KEY'],
    rootCause: 'A credential-like value is embedded in source code.',
    rootCauseAr: 'قيمة حساسة شبيهة ببيانات الاعتماد مضمنة مباشرة داخل الكود المصدري.',
    exploitability: 'Configuration exposure risk',
    exploitabilityAr: 'خطر كشف إعدادات حساسة',
    evidence: 'Secret material is present in source.',
    evidenceAr: 'توجد قيمة حساسة داخل الملف المصدري.',
    weakCode: `SECRET_KEY = "DEMO_PLACEHOLDER_VALUE"`,
    secureCode: `SECRET_KEY = os.environ["SECRET_KEY"]`,
    changedLines: '1 line',
    originalFileName: 'config.py',
    language: 'Python',
    updateAction: 'secret_management_fix',
    modification: 'Security Fix',
    modificationAr: 'إصلاح أمني',
    updatedFileContent: `import os

class Config:
    DEBUG = False
    SECRET_KEY = os.environ["SECRET_KEY"]
    DATABASE_URL = os.getenv("DATABASE_URL")`,
    verification: {
      functional: 'Pending environment validation',
      replay: 'Not applicable',
      rescan: 'Pending',
      retrace: 'Not applicable',
      closure: 'Candidate fix',
    },
  },
];

export const mockLiveOperation = {
  stage: 'Investigate',
  title: 'Tracing a user-controlled identifier through authorization boundaries',
  action: 'Following user_id from the Flask route into UserService and repository access.',
  discovery: 'Authentication is present. Ownership authorization is not visible on the path.',
  why: 'Authentication proves identity; it does not prove access to another user resource.',
};

export const mockReport = {
  executive: {
    initialFindings: 6,
    currentFindings: 3,
    criticalBefore: 1,
    criticalAfter: 0,
    verifiedRemediated: 3,
    remaining: 3,
    coverage: '96%',
    evidenceCoverage: '83%',
    residualRisk: 'Medium',
  },
  technology: {
    language: 'Python 3.12',
    framework: 'Flask 3.x',
    architecture: 'Layered web application',
    database: 'PostgreSQL',
    dependencies: 37,
  },
  standards: ['CWE', 'OWASP Top 10', 'OWASP ASVS'],
  aiMatrix: [
    ['Code explanation', 'AI assisted'],
    ['Finding detection', 'Deterministic scanner'],
    ['Finding correlation', 'AI assisted'],
    ['Fix proposal', 'AI assisted'],
    ['Verification', 'Deterministic evidence'],
    ['Closure decision', 'Evidence based'],
  ],
  findings: mockFindings,
};

export const mockConfiguration = {
  aiProvider: 'Backend-managed provider',
  aiModel: 'BACKEND_CONTRACT_REQUIRED',
  aiRoles: [
    'Code explanation',
    'Finding correlation',
    'Root-cause reasoning',
    'Secure candidate generation',
  ],
  scanProfile: 'Deep',
  scanProfiles: ['Quick', 'Standard', 'Deep'],
  standardsPack: 'CWE + OWASP Top 10 + ASVS',
  note: 'API keys and model credentials must be stored by the backend, never in React.',
  connectionState: 'Not connected in frontend-only build',
};

export const mockAnalysisProgress = {
  projectName: 'Customer Portal',
  sourceLabel: 'customer-portal.zip',
  stages: [
    {
      id: 'fingerprint',
      label: 'Fingerprint project',
      labelAr: 'تحديد البصمة التقنية',
      detail: 'Detect language, framework, dependencies, database signals, and entry points.',
      detailAr: 'تحديد اللغة والإطار والاعتماديات وإشارات قاعدة البيانات ونقاط الدخول.',
      result: 'Python 3.12 · Flask 3.x · PostgreSQL · 42 files',
      resultAr: 'Python 3.12 · Flask 3.x · PostgreSQL · 42 ملفًا',
    },
    {
      id: 'understand',
      label: 'Understand code',
      labelAr: 'فهم بنية الكود',
      detail: 'Map files, functions, routes, and security-sensitive operations.',
      detailAr: 'ربط الملفات والدوال والمسارات والعمليات الحساسة أمنيًا.',
      result: '118 functions · 17 routes · 4 sensitive areas',
      resultAr: '118 دالة · 17 مسارًا · 4 مناطق حساسة',
    },
    {
      id: 'scan',
      label: 'Run scanner profile',
      labelAr: 'تنفيذ ملف الفحص',
      detail: 'Apply the selected frontend preview profile and standards mapping.',
      detailAr: 'تطبيق ملف الفحص التجريبي وربط النتائج بالمعايير الأمنية.',
      result: '186 rules represented in demo data · 96% mock coverage',
      resultAr: '186 قاعدة ضمن بيانات العرض · تغطية تجريبية 96%',
    },
    {
      id: 'correlate',
      label: 'Correlate findings',
      labelAr: 'ربط النتائج بالسياق',
      detail: 'Attach scanner findings to files, functions, lines, and application context.',
      detailAr: 'ربط نتائج الفحص بالملفات والدوال والأسطر وسياق التطبيق.',
      result: '3 findings mapped to code context',
      resultAr: '3 نتائج مرتبطة بسياق الكود',
    },
    {
      id: 'prepare',
      label: 'Prepare workbench',
      labelAr: 'تجهيز مساحة العمل',
      detail: 'Organize code, findings, standards, and evidence for review.',
      detailAr: 'تنظيم الكود والنتائج والمعايير والأدلة للمراجعة البشرية.',
      result: 'Secure Workbench ready for human review',
      resultAr: 'مساحة العمل الأمنية جاهزة للمراجعة',
    },
  ],
  note: 'Frontend preview only. Real stage events and counts require a backend contract.',
};
