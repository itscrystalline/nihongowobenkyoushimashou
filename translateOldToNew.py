import json

files = ["old_json_file/N5.json","old_json_file/N4.json","old_json_file/N3.json"]
saves = ["new_json_file/N5.json","new_json_file/N4.json","new_json_file/N3.json"]
alphabet = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]

# This file is super hard-coding, you must optimize it yourself in order run property.
# Thus, this code will take forever to run. (O(n^5))

for file_index in range(0,3):
    with open(files[file_index],encoding="utf8") as open_file:
        with open(saves[file_index],encoding="utf8",mode="w") as save_file:
            words = []
            new_data = {"cards":[]}
            old_data = json.load(open_file)
            old_data = old_data["pools"]
            for card_set in old_data:
                cards = card_set["cards"]
                for card in cards:
                    word, meaning = card["side1"], card["side2"].replace("\n", " ").replace("  "," ")
                    for char in card["side1"]:
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
                    else:
                        new_word = True
                        try:
                            for word2 in words:
                                index = words.index(word2)
                                for meaning3 in new_data["cards"][index]["meaning"]:
                                    if (word in word2 or word2 in word) and (meaning3 in meaning or meaning in meaning3):
                                        new_word = False
                                        if meaning3 in meaning:
                                            new_data["cards"][index]["meaning"][new_data["cards"][index]["meaning"].index(meaning3)] = meaning
                                        else:
                                            continue

                        except:
                            pass
                        if new_word:
                            words.append(word)
                            index = words.index(word)
                            new_data["cards"].append({"word":"","meaning":[],"score":0})
                            new_data["cards"][index]["word"] = word
                            new_data["cards"][index]["meaning"].append(meaning)
                new_data["cards"][index]["score"] = 0
            json.dump(new_data,save_file,ensure_ascii=False,indent=4)