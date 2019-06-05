jsonata = require('jsonata')

let data = {
    'image': 123
}

let expression = jsonata('image > 100')
console.log(expression.evaluate(data))
