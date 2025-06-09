declare module '@babel/standalone' {
  interface TransformOptions {
    presets?: string[];
    plugins?: string[];
    filename?: string;
    ast?: boolean;
    code?: boolean;
    sourceMaps?: boolean;
    sourceType?: 'script' | 'module' | 'unambiguous';
    sourceFileName?: string;
    sourceMapTarget?: string;
    retainLines?: boolean;
    compact?: boolean | 'auto';
    minified?: boolean;
    comments?: boolean;
    shouldPrintComment?: (comment: string) => boolean;
    parserOpts?: Record<string, any>;
    generatorOpts?: Record<string, any>;
  }

  interface TransformResult {
    code: string;
    ast?: any;
    map?: any;
  }

  export function transform(code: string, options?: TransformOptions): TransformResult;
  export function transformFromAst(ast: any, code: string, options?: TransformOptions): TransformResult;
  export function parse(code: string, options?: TransformOptions): any;
  export function registerPlugin(name: string, plugin: any): void;
  export function registerPreset(name: string, preset: any): void;
} 