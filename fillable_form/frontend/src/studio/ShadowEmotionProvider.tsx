import { ReactNode, useLayoutEffect, useRef, useState } from 'react';
import createCache, { type EmotionCache } from '@emotion/cache';
import { CacheProvider } from '@emotion/react';

/**
 * react-select styles itself with emotion, which by default injects its
 * <style> tags into document.head. Inside a shadow DOM those styles would not
 * apply, so this points emotion at the shadow root that contains the app.
 */
export function ShadowEmotionProvider({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [cache, setCache] = useState<EmotionCache | null>(null);

  useLayoutEffect(() => {
    const rootNode = ref.current?.getRootNode();
    const container = rootNode instanceof ShadowRoot ? rootNode : document.head;
    setCache(createCache({ key: 'fillable-form', container }));
  }, []);

  return (
    <div ref={ref}>
      {cache && <CacheProvider value={cache}>{children}</CacheProvider>}
    </div>
  );
}
