/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Noto Serif SC', 'STSong', 'SimSun', ' serif'],
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        // 主题色
        brand: {
          primary: 'var(--brand-primary)',
          dark: 'var(--brand-dark)',
          light: 'var(--brand-light)',
        },
        // 强调色
        accent: {
          primary: 'var(--accent-primary)',
          success: 'var(--accent-success)',
          warning: 'var(--accent-warning)',
          error: 'var(--accent-error)',
          info: 'var(--accent-info)',
        },
        // 背景色
        surface: {
          page: 'var(--bg-page)',
          container: 'var(--bg-container)',
          secondary: 'var(--bg-secondary)',
          hover: 'var(--bg-hover)',
          selected: 'var(--bg-selected)',
          disabled: 'var(--bg-disabled)',
        },
        // 文字色
        content: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          tertiary: 'var(--text-tertiary)',
          disabled: 'var(--text-disabled)',
          inverse: 'var(--text-inverse)',
        },
        // 边框色
        line: {
          default: 'var(--border-default)',
          hover: 'var(--border-hover)',
          focus: 'var(--border-focus)',
          active: 'var(--border-active)',
        },
        // 兼容旧名称
        black: '#000000',
        white: '#FFFFFF',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
      borderRadius: {
        'sm': 'var(--radius-sm)',
        'md': 'var(--radius-md)',
        'lg': 'var(--radius-lg)',
        'xl': 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
        'full': 'var(--radius-full)',
      },
      boxShadow: {
        'sm': 'var(--shadow-sm)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'xl': 'var(--shadow-xl)',
      },
      transitionDuration: {
        'fast': '150ms',
        'normal': '200ms',
        'slow': '300ms',
      },
    },
  },
  plugins: [],
}