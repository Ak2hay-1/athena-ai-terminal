/** Simple object pool to avoid allocations in hot render paths. */
export class ObjectPool<T> {
  private free: T[] = [];
  private readonly factory: () => T;
  private readonly reset: (item: T) => void;

  constructor(factory: () => T, reset: (item: T) => void, initial = 0) {
    this.factory = factory;
    this.reset = reset;
    for (let i = 0; i < initial; i++) this.free.push(factory());
  }

  acquire(): T {
    return this.free.pop() ?? this.factory();
  }

  release(item: T): void {
    this.reset(item);
    this.free.push(item);
  }
}

/** Scratch number arrays reused across frames. */
export function createNumberScratch(size = 64): {
  get: (len: number) => number[];
} {
  let buf = new Array<number>(size);
  return {
    get(len: number) {
      if (buf.length < len) buf = new Array<number>(len);
      return buf;
    },
  };
}
