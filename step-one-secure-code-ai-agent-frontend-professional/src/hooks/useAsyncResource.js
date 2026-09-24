import { useCallback, useEffect, useState } from 'react';

export default function useAsyncResource(loader, dependencies = []) {
  const [state, setState] = useState({
    data: null,
    error: null,
    loading: true,
  });

  const load = useCallback(async () => {
    setState((current) => ({ ...current, error: null, loading: true }));

    try {
      const data = await loader();
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({
        data: null,
        error: error instanceof Error ? error : new Error('Unknown frontend error'),
        loading: false,
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  useEffect(() => {
    load();
  }, [load]);

  return {
    ...state,
    reload: load,
  };
}
