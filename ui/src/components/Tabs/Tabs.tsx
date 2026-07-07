import type { ReactNode } from 'react';
import styles from './Tabs.module.css';

export interface TabDef<T extends string> {
  id: T;
  label: ReactNode;
}

interface TabsProps<T extends string> {
  tabs: TabDef<T>[];
  active: T;
  onChange: (id: T) => void;
  variant?: 'section' | 'sub';
}

export function Tabs<T extends string>({
  tabs,
  active,
  onChange,
  variant = 'section',
}: TabsProps<T>) {
  const wrapClass = variant === 'sub' ? styles.subTabs : styles.tabs;
  const btnClass = variant === 'sub' ? styles.subTabBtn : styles.tabBtn;
  return (
    <div className={wrapClass}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`${btnClass} ${active === tab.id ? styles.active : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
