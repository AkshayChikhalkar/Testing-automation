import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import translation files
import en from './locales/en.json';
import de from './locales/de.json';
import es from './locales/es.json';
import fr from './locales/fr.json';
import zh from './locales/zh.json';

const resources = {
  en: {
    translation: en,
  },
  de: {
    translation: de,
  },
  es: {
    translation: es,
  },
  fr: {
    translation: fr,
  },
  zh: {
    translation: zh,
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en', // default language
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    
    interpolation: {
      escapeValue: false, // React already does escaping
    },
    
    // Namespace configuration
    defaultNS: 'translation',
    ns: ['translation'],
  });

export default i18n;
