import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const translations = {
  en: {
    brand: 'SecClosure',
    arabicBrand: 'رقيب',
    language: 'العربية',
    launch: 'Launch Raqeeb',
    signIn: 'Sign in',
    projects: 'Projects',
    newAnalysis: 'New analysis',
    reports: 'Reports',
    configuration: 'Configuration',
    workbench: 'Secure Workbench',
    mock: 'Frontend preview',
    project: 'Project',
    report: 'Security report',
    openWorkbench: 'Open workbench',
    startAnalysis: 'Prepare analysis',
    backToProjects: 'Back to projects',
    printReport: 'Print / Save PDF',
    aiEngine: 'AI engine',
    scanProfile: 'Scan profile',
    standardsPack: 'Standards pack',
    savePreview: 'Save preview',
  },
  ar: {
    brand: 'SecClosure',
    arabicBrand: 'رقيب',
    language: 'English',
    launch: 'تشغيل رقيب',
    signIn: 'تسجيل الدخول',
    projects: 'المشاريع',
    newAnalysis: 'تحليل جديد',
    reports: 'التقارير',
    configuration: 'الإعدادات',
    workbench: 'مساحة العمل الأمنية',
    mock: 'نسخة Frontend',
    project: 'المشروع',
    report: 'التقرير الأمني',
    openWorkbench: 'فتح مساحة العمل',
    startAnalysis: 'تجهيز التحليل',
    backToProjects: 'العودة للمشاريع',
    printReport: 'طباعة / حفظ PDF',
    aiEngine: 'محرك الذكاء الاصطناعي',
    scanProfile: 'ملف الفحص',
    standardsPack: 'حزمة المعايير',
    savePreview: 'حفظ العرض',
  },
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('ar');

  useEffect(() => {
    const direction = language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = language;
    document.documentElement.dir = direction;
  }, [language]);

  const value = useMemo(() => {
    const t = (key) => translations[language][key] ?? key;
    const toggleLanguage = () => {
      setLanguage((current) => (current === 'en' ? 'ar' : 'en'));
    };

    return {
      language,
      direction: language === 'ar' ? 'rtl' : 'ltr',
      t,
      toggleLanguage,
    };
  }, [language]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error('useLanguage must be used inside LanguageProvider');
  }

  return context;
}
