import { useI18n } from '@/i18n/context'
import { LANGS } from '@/i18n/dictionary'
import styles from './LanguageToggle.module.css'

export function LanguageToggle() {
  const { lang, setLang, t } = useI18n()
  return (
    <div role="group" aria-label={t.common.language} className={styles.toggle}>
      {LANGS.map((option) => (
        <button
          key={option}
          type="button"
          lang={option}
          aria-pressed={lang === option}
          className={styles.option}
          onClick={() => setLang(option)}
        >
          {option.toUpperCase()}
        </button>
      ))}
    </div>
  )
}
