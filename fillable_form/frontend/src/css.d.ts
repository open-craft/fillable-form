// The learner bundle imports CSS as a plain string (css-loader with
// exportType "string") to inject it into the block's shadow DOM.
declare module '*.css' {
  const content: string;
  export default content;
}
