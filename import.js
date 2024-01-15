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

    if (term) {
        // delete term from json
        json.pools = json.pools.filter(t => t.id !== id)
        console.log("deleted old term")
    }

    let pool = {
        id: id,
        cards: []
    }
    for (var i = 0; i < terms.length; i++) {
        if (terms[i].cardSides[0].media[1]?.url)
            downloadImage(terms[i].cardSides[0].media[1].url, `./${level}`)
                .then(r => console.log("downloaded image"))
        if (terms[i].cardSides[1].media[1]?.url)
            downloadImage(terms[i].cardSides[1].media[1].url, `./${level}`)
                .then(r => console.log("downloaded image"))
        const card = {
            side1: terms[i].cardSides[0].media[0].plainText,
            side2: terms[i].cardSides[1].media[0].plainText,
            side1image: terms[i].cardSides[0].media[1]?.url ? __dirname + `/${level}/${terms[i].cardSides[0].media[1].url.split("/").pop()}` : "",
            side2image: terms[i].cardSides[1].media[1]?.url ? __dirname + `/${level}/${terms[i].cardSides[1].media[1].url.split("/").pop()}` : "",
            score: 0
        }
        pool.cards.push(card)
    }
    json.pools.push(pool)

    fs.writeFileSync(`./${level}.json`, JSON.stringify(json))
}

async function downloadImage(url, folderName) {
    const fs = require("fs");
    const {mkdir} = require("fs/promises");
    const {Readable} = require('stream');
    const {finished} = require('stream/promises');
    const path = require("path");

    try {
        const res = await fetch(url);
        const fileName = path.basename(url);
        if (!fs.existsSync(folderName)) await mkdir(folderName); //Optional if you already have downloads directory
        const destination = path.resolve("./" + folderName, fileName);
        if (fs.existsSync(destination)) return;
        const fileStream = fs.createWriteStream(destination, {flags: 'wx'});
        await finished(Readable.fromWeb(res.body).pipe(fileStream));
    } catch (err) {
        console.log(err)
    }
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
