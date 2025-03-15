module.exports = {
  presets: ['next/babel'],
  plugins: [
    [
      'module-resolver',
      {
        root: ['.'],
        alias: {
          '@': './src',
          '@/lib': './src/lib',
          '@/components': './src/components',
          '@/app': './src/app'
        },
        extensions: [
          '.js',
          '.jsx',
          '.ts',
          '.tsx',
        ]
      }
    ]
  ]
}; 