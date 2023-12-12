import json

import QuizletAPI

files: dict = {
    "N5.json": [
        182218890,
        3013578,
        496298421
    ],
    "N4.json": [
        121982607,
        16963863,
        319934698
    ],
    "N3.json": [
        5920504
    ]
}

fileData = {
    "cards": [

    ]
}

alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
            "v", "w", "x", "y", "z"]
for file, IDs in files.items():
    words = []
    # if os.path.exists(file):
    #     print("Conflict\n"
    #           f"{file} already have been created\n"
    #           "Moving to the next file...")
    with open(file, mode="w+", encoding="utf8") as openFile:
        new_data = {"cards": []}
        print("Starting", file)
        print("-" * 60)
        for ID in IDs:
            tokens = ["", ]
            # Token Get
            print("New ID", str(ID))
            print("-" * 60)
            data = QuizletAPI.GetDataByID(ID)
            token = QuizletAPI.GetTokenByData(data)
            tokens.append(token)
            for page in range(0, QuizletAPI.GetTotalCardsByData(data), 500):
                print("Current file  : ", file)
                print("Current page  : ", page, "/", QuizletAPI.GetTotalCardsByData(data))
                print("Current ID    : ", ID)
                print("Current Index : ", files[file].index(ID) + 1, "/", files[file].__len__())
                print("-" * 60)
                pageData = QuizletAPI.GetDataByID(ID, perpage=500, page=page // 500 + 1, token=tokens[-1])
                cardSet = QuizletAPI.GetCardSetByData(pageData)
                tokens.append(QuizletAPI.GetTokenByData(pageData))
                for card in cardSet:
                    card = QuizletAPI.Card(card)
                    word, meaning = card.GetText(1), card.GetText(2).replace("\n", " ").replace(";", " ").replace("  ",
                                                                                                                  " ").replace(
                        "  ", " ")
                    for char in word:
                        if char.lower() in alphabet:
                            word, meaning = meaning, word
                            break
                    if word in words:
                        index = words.index(word)
                        if meaning in new_data["cards"][index]["meaning"]:
                            pass
                        else:
                            for meaning2 in new_data["cards"][index]["meaning"]:
                                if meaning in meaning2 or meaning2 in meaning:
                                    break
                            else:
                                new_data["cards"][index]["meaning"].append(meaning)
                                new_data["cards"][index]["meaningTTS"].append(card.GetUrlTextToSpeech(2, "Normal"))
                                new_data["cards"][index]["meaningSlowTTS"].append(card.GetUrlTextToSpeech(2, "Slow"))
                    else:
                        new_word = True
                        try:
                            for word2 in words:
                                index = words.index(word2)
                                for meaning3 in new_data["cards"][index]["meaning"]:
                                    if (word in word2 or word2 in word) and (
                                            meaning3 in meaning or meaning in meaning3):
                                        new_word = False
                                        if meaning3 in meaning:
                                            new_data["cards"][index]["meaning"][
                                                new_data["cards"][index]["meaning"].index(meaning3)] = meaning
                                            new_data["cards"][index]["meaningTTS"][
                                                new_data["cards"][index]["meaning"].index(
                                                    meaning3)] = card.GetUrlTextToSpeech(2, "Normal")
                                            new_data["cards"][index]["meaningSlowTTS"][
                                                new_data["cards"][index]["meaning"].index(
                                                    meaning3)] = card.GetUrlTextToSpeech(2, "Slow")
                                        else:
                                            continue

                        except:
                            pass
                        if new_word:
                            words.append(word)
                            index = words.index(word)
                            new_data["cards"].append(
                                {"word": word, "meaning": [meaning], "wordTTS": [card.GetUrlTextToSpeech(1, "Normal")],
                                 "wordSlowTTS": [card.GetUrlTextToSpeech(1, "Slow")],
                                 "meaningTTS": [card.GetUrlTextToSpeech(2, "Normal")],
                                 "meaningSlowTTS": [card.GetUrlTextToSpeech(2, "Slow")], "score": 0})
        openFile.write(json.dumps(new_data, ensure_ascii=False, indent=4))
        print("Finished ", file)
        print("-" * 60)
