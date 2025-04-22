module.exports = {
  plugins: [
    "@babel/plugin-proposal-optional-chaining",
    "@babel/plugin-proposal-nullish-coalescing-operator"
  ]
}
const num = [1,2,3,4]
let aaa = [...num]