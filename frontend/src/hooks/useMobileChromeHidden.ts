import { useEffect, useRef, useState } from 'react'

type Options = {
  topThreshold?: number
  deltaThreshold?: number
}

export function useMobileChromeHidden(options?: Options) {
  const { topThreshold = 24, deltaThreshold = 12 } = options ?? {}
  const [mobileChromeHidden, setMobileChromeHidden] = useState(false)
  const lastScrollYRef = useRef(0)

  useEffect(() => {
    lastScrollYRef.current = 0
    setMobileChromeHidden(false)

    const mediaQuery = window.matchMedia('(max-width: 767px)')

    const handleScrollDirection = () => {
      if (!mediaQuery.matches) {
        setMobileChromeHidden(false)
        lastScrollYRef.current = window.scrollY
        return
      }

      const currentScrollY = window.scrollY
      const delta = currentScrollY - lastScrollYRef.current

      if (currentScrollY <= topThreshold) {
        setMobileChromeHidden(false)
        lastScrollYRef.current = currentScrollY
        return
      }

      if (Math.abs(delta) < deltaThreshold) {
        return
      }

      setMobileChromeHidden(delta > 0)
      lastScrollYRef.current = currentScrollY
    }

    const handleViewportChange = () => {
      if (!mediaQuery.matches) {
        setMobileChromeHidden(false)
      }
      lastScrollYRef.current = window.scrollY
    }

    lastScrollYRef.current = window.scrollY
    window.addEventListener('scroll', handleScrollDirection, { passive: true })
    mediaQuery.addEventListener('change', handleViewportChange)

    return () => {
      window.removeEventListener('scroll', handleScrollDirection)
      mediaQuery.removeEventListener('change', handleViewportChange)
    }
  }, [deltaThreshold, topThreshold])

  return mobileChromeHidden
}
