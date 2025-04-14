module.exports = {
  presets: [
    '@vue/cli-plugin-babel/preset',
      ['@babel/preset-react', {
      runtime: 'automatic'
    }]
  ],
  plugins: ['@vue/babel-plugin-jsx']

}
