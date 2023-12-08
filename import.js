async function quizlet(id, level) {
    let res = await fetch(`https://quizlet.com/webapi/3.4/studiable-item-documents?filters%5BstudiableContainerId%5D=${id}&filters%5BstudiableContainerType%5D=1&perPage=500&page=1`).then(res => res.json())
    let currentLength = res.responses[0].models.studiableItem.length
    let token = res.responses[0].paging.token
    let terms = res.responses[0].models.studiableItem
    let page = 2
    console.log("page 1 done")
    while (currentLength >= 500) {
        let res = await fetch(`https://quizlet.com/webapi/3.4/studiable-item-documents?filters%5BstudiableContainerId%5D=${id}&filters%5BstudiableContainerType%5D=1&perPage=500&page=${page++}&pagingToken=${token}`).then(res => res.json())
        terms.push(...res.responses[0].models.studiableItem)
        currentLength = res.responses[0].models.studiableItem.length
        token = res.responses[0].paging.token
        console.log(`page ${page - 1} done`)
    }
    return {id, level, terms}
}

function addToFile({id, level, terms}) {
    let fs = require("fs")

    // copy example.json to level.json if level.json doesn't exist
    if (!fs.existsSync(`./${level}.json`)) {
        fs.copyFileSync("./example.json", `./${level}.json`)
    }

    let data = fs.readFileSync(`./${level}.json`, "utf8")
    let json = JSON.parse(data)
    let term = json.pools.find(t => t.id === id)
    if (!term) {
        let pool = {
            id: id,
            length: terms.length,
            cards: []
        }
        for (var i = 0; i < terms.length; i++) {
            const card = {
                side1: terms[i].cardSides[0].media[0].plainText,
                side2: terms[i].cardSides[1].media[0].plainText,
                score: 0
            }
            pool.cards.push(card)
        }
        json.pools.push(pool)
    }
    fs.writeFileSync(`./${level}.json`, JSON.stringify(json))
}


const args = process.argv.slice(2)
console.log(args)
let parsedArgs = []
for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("-")) {
        parsedArgs.push([args[i]])
    } else {
        parsedArgs[parsedArgs.length - 1].push(args[i])
    }
}
parsedArgs.forEach(arg => {
    if (arg[0] === "--level" || arg[0] === "-l") {
        let level = arg[1]
        let ids = arg.slice(2)
        ids.forEach(id => {
            let intId = parseInt(id)
            console.log(`fetching ${intId} ${level}`)
            quizlet(intId, level).then(r => addToFile(r))
        })
    }
})

// quizlet(5920504, "N3").then(r => addToFile(r))
//
// quizlet(182218890, "N5").then(r => addToFile(r))
// quizlet(3013578, "N5").then(r => addToFile(r))
// quizlet(496298421, "N5").then(r => addToFile(r))
//
// quizlet(121982607, "N4").then(r => addToFile(r))
// quizlet(16963863, "N4").then(r => addToFile(r))
// quizlet(319934698, "N4").then(r => addToFile(r))
