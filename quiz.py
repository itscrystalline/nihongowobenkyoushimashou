import copy
import json
import random
import time
import sys

from inspect import currentframe
from colorama import Fore, Back, Style
from itertools import combinations


class QuizSession:

    def getLine(self):
        cf = currentframe()
        return cf.f_back.f_lineno

    def __init__(self, args: list):
        self.loadedFile = ""
        self.lengths = []
        self.loadedData = {}
        self.questions = []
        self.interpreted = {}

        self.debug = False
        self.colorize = True

        self.interpreted = self.interpretArgs(args)

        start = time.time()
        # extra argument handling
        if "file" in self.interpreted:
            if "toClear" in self.interpreted:
                print(self.col(Fore.YELLOW) + "Clearing scores from", self.interpreted["file"] + self.col(Fore.RESET))
                self.loadSet(self.interpreted["file"])
                for pool in self.loadedData:
                    for card in pool["cards"]:
                        card["score"] = 0
                self.saveSet(self.interpreted["file"])
                print(self.col(Fore.GREEN) + "Done!" + self.col(Fore.RESET))
                quit(0)
            file = self.interpreted["file"]
            numRandom = self.interpreted["numCards"] if "numCards" in self.interpreted else 20
        elif "dir" in self.interpreted:
            dirName = self.interpreted["dir"]
            files = [[dirName + "N5.json", 20], [dirName + "N4.json", 10], [dirName + "N3.json", 5]]
            fileWeights = [0.5, 0.25, 0.125]

            result = random.choices(files, weights=fileWeights, k=1)[0]
            file = result[0]
            numRandom = result[1]
        else:
            files = [["N5.json", 20], ["N4.json", 10], ["N3.json", 5]]
            fileWeights = [0.5, 0.25, 0.125]

            result = random.choices(files, weights=fileWeights, k=1)[0]
            file = result[0]
            numRandom = result[1]

        # load the json file
        self.debugPrint("Loading", file, "with", numRandom, "random cards", self.getLine())
        print(self.col(Fore.CYAN), "=========>", file[:-5], f"({numRandom} questions)", "<=========")
        self.loadedFile = file
        self.loadSet(file)

        # pick random cards
        randomCards = self.getCardsRandom(numRandom)
        self.questions = self.getQuestions(randomCards)
        self.debugPrint(self.questions, self.getLine())

        end = time.time()
        self.debugPrint("Preparation done in", end - start, "ms.", self.getLine())

    def getLoadedQuestions(self) -> list:
        return self.questions

    def col(self, code: str) -> str:
        return code if self.colorize else ""

    def debugPrint(self, *args) -> None:
        if self.debug:
            print(f"{self.col(Fore.RED)}[quiz.py:{args[-1]}]{self.col(Fore.YELLOW)}", *args[:-1],
                  self.col(Style.RESET_ALL))

    def loadSet(self, target: str) -> None:
        with open(target, encoding='utf8') as f:
            data = json.load(f)
            pools = data["pools"]
            self.loadedData = pools
            for pool in pools:
                self.lengths.append(len(pool["cards"]))

            self.debugPrint("Loaded", len(pools), "quiz pools with", sum(self.lengths), "cards total", self.getLine())
            self.debugPrint("Lengths:", self.lengths, self.getLine())

    def saveSet(self, target=None) -> None:
        if "dryRun" in self.interpreted and "toClear" not in self.interpreted:
            print(self.col(Fore.YELLOW) + "Dry run enabled, not saving!" + self.col(Fore.RESET))
            return

        if target is None:
            target = self.loadedFile

        with open(target, "w", encoding='utf8') as opened:
            toSave = {
                "pools": self.loadedData
            }
            json.dump(toSave, opened, ensure_ascii=False, indent=4)

    def getCard(self, index: int) -> dict:
        pool_index: int = 0
        all_cards: int = 0
        for set_index, number_of_cards in enumerate(self.lengths):
            all_cards += number_of_cards
            if index > all_cards:
                pass
            else:
                all_cards -= number_of_cards
                pool_index = set_index
                break

        card = self.loadedData[pool_index]["cards"][index - all_cards]
        card["pool_id"] = pool_index
        card["global_index"] = index
        card["local_index"] = index - all_cards

        return {
            "side1": card["side1"],
            "side2": card["side2"],
            "score": card["score"],
            "pool_id": pool_index,
            "global_index": index,
            "local_index": index - all_cards,
        }

    def setCardScore(self, index: int, score: int) -> None:
        card = self.getCard(index)
        self.debugPrint(card, self.getLine())
        localIndex = card["local_index"]
        self.debugPrint(localIndex, self.getLine())
        self.loadedData[card["pool_id"]]["cards"][localIndex] = {
            "side1": card["side1"],
            "side2": card["side2"],
            "score": score
        }

    def getCardsRandom(self, num: int) -> list:
        # weighed random from card scores
        indices = []
        scores = []
        indexCount = 0
        cards = []
        for pool in self.loadedData:
            for card in pool["cards"]:
                indices.append(indexCount)
                indexCount += 1
                if "reverseWeights" in self.interpreted:
                    scores.append(2 + ((card["score"] + 10) * 0.9))
                else:
                    scores.append(2 + ((20 - (card["score"] + 10)) * 0.9))
        sumScores = sum(scores)
        weights = [(score / sumScores) * 100 for score in scores]
        self.debugPrint("Scores:", scores, self.getLine())
        self.debugPrint("Weights:", weights, self.getLine())
        self.debugPrint("Indices:", indices, self.getLine())
        randomIndices = random.choices(indices, weights=weights, k=num)
        self.debugPrint("Random Indices:", randomIndices, self.getLine())
        for index in randomIndices:
            cards.append(self.getCard(index))

        return cards

    def getCardsRandomFromPool(self, pool: int, num: int, excludesLocalIndex: int = None) -> list:
        cards = copy.deepcopy(self.loadedData[pool]["cards"])
        if excludesLocalIndex is not None:
            for localIndex, card in enumerate(cards):
                if localIndex == excludesLocalIndex:
                    cards.remove(card)
                    break

        return random.choices(cards, k=num)

    def getQuestions(self, cards: list) -> list:
        questionsToReturn = []
        for card in cards:
            poolId = card["pool_id"]
            randomInPool = self.getCardsRandomFromPool(poolId, 3, card["local_index"])
            # filter out duplicates within the random cards
            isValid = False
            while not isValid:
                isValid = True
                for combo in combinations(randomInPool, 2):
                    if combo[0]["side2"] == combo[1]["side2"]:
                        self.debugPrint("Duplicate found:", combo[0]["side2"], "and", combo[1]["side2"], self.getLine())
                        randomInPool = self.getCardsRandomFromPool(poolId, 3, card["local_index"])
                        isValid = False
                        break

            answers = [card["side2"]] + [cardRandom["side2"] for cardRandom in randomInPool]
            random.shuffle(answers)
            question = {
                "question": card["side1"],
                "answers": answers,
                "correct": card["side2"],
                "global_index": card["global_index"],
                "score": card["score"],
            }
            questionsToReturn.append(question)

        return questionsToReturn

    def interpretArgs(self, args: list[str]) -> dict[str, str]:
        self.debug = "--debug" in args or "-d" in args if len(sys.argv) > 1 else False
        self.debugPrint("Debug mode enabled!", self.getLine())
        self.debugPrint("Raw Arguments:", args, self.getLine())

        parsedArgs = []
        for arg in args:
            if arg == "--debug" or arg == "-d":
                continue

            if arg.startswith("-"):
                parsedArgs.append([arg])
            else:
                parsedArgs[-1].append(arg)

        self.debugPrint("Parsed Arguments:", parsedArgs, self.getLine())

        interpreted = {}
        for argGroup in parsedArgs:
            if argGroup[0] == "--debug" or argGroup[0] == "-d":
                continue
            elif argGroup[0] == "--clear":
                interpreted["toClear"] = True
            elif argGroup[0] == "--help" or argGroup[0] == "-h":
                print("Usage: python quiz.py [options]")
                print("Options:")
                print("  --help, -h: Display this help message.")
                print("  --debug, -d: Enable debug mode.")
                print("  --clear: Clear all scores from the file specified in --file. If --file is not specified, "
                      "this will be ignored.")
                print("  --file, -f: Load a specific file from a path.")
                print("  --dir, -D: Set a specific root directory to load files from. If --file is also specified, "
                      "this will be ignored.")
                print("  --num-cards, -n: Load a specific number of cards, default is 20.")
                print("  --no-colorize, -N: Disable colorization.")
                print("  --dry-run: Do not save any changes. If --clear is specified, this will be ignored.")
                print("  --reverse-weights, -r: Reverse the weights for the random card selection. This will make "
                      "cards with higher scores more likely to be chosen.")
                quit(0)
            elif argGroup[0] in ["--dir", "-D"]:
                if len(argGroup) < 2:
                    print("FATAL: No directory name provided to load!")
                    quit(1)

                if not argGroup[1].endswith("/"):
                    argGroup[1] += "/"

                dirName = argGroup[1]
                interpreted["dir"] = dirName
            elif argGroup[0] in ["--file", "-f"]:
                if len(argGroup) < 2:
                    print("FATAL: No file name provided to load!")
                    quit(1)

                if not argGroup[1].endswith(".json"):
                    print("FATAL: File name provided is not a .json file!")
                    quit(1)

                fileName = argGroup[1]
                interpreted["file"] = fileName

            elif argGroup[0] in ["--num-cards", "-n"]:
                if len(argGroup) < 2:
                    print("FATAL: No number provided!")
                    quit(1)

                try:
                    numCards = int(argGroup[1])
                except ValueError:
                    print("FATAL: Number of cards provided is not an integer!")
                    quit(1)

                interpreted["numCards"] = numCards

            elif argGroup[0] in ["--no-colorize", "-N"]:
                self.colorize = False
            elif argGroup[0] == "--dry-run":
                interpreted["dryRun"] = True
            elif argGroup[0] in ["--reverse-weights", "-r"]:
                interpreted["reverseWeights"] = True
            else:
                print("WARNING: Unknown argument:", argGroup[0], "Continuing...")
                continue

        return interpreted


def mainLoop(session: QuizSession) -> None:
    questions = session.getLoadedQuestions()
    # ik session.questions work but fuck you, getters ftw!!!!!!!!!!! /s

    correctAnswers = 0
    quitEarly = False
    for num, question in enumerate(questions):
        print(session.col(Fore.CYAN), num + 1, "/", len(questions), ". ", session.col(Fore.LIGHTWHITE_EX),
              session.col(Back.BLACK),
              question["question"], " (", question["score"], ")", session.col(Style.RESET_ALL), sep="")
        spaces = " " * (len(str(num + 1)) + 5)
        correctAnswerIndex = -1
        for index, answer in enumerate(question["answers"]):
            print(f"{session.col(Style.BRIGHT)}{spaces}{index + 1}{session.col(Style.RESET_ALL)}. {answer}")
            if answer == question["correct"]:
                correctAnswerIndex = index + 1

        userAnswer = ""
        isValid = False
        while not isValid:
            userAnswer = input(session.col(Fore.CYAN) + "Answer (1-4, n for don't know): " + session.col(Fore.RESET))
            isValid = userAnswer == "q" or userAnswer == "n" or (userAnswer.isdigit() and 1 <= int(userAnswer) <= 4)
            print(session.col(Fore.RED) + "Invalid input!" + session.col(Fore.RESET)) if not isValid else None

        if userAnswer == "q":
            print(session.col(Fore.RED) + "You quit early!" + session.col(Fore.RESET))
            print(session.col(Fore.LIGHTYELLOW_EX) + "You answered", correctAnswers, "questions correctly out of", num,
                  "question(s)." + session.col(Fore.RESET))
            quitEarly = True
            break

        if userAnswer == "n":
            print(session.col(Fore.LIGHTRED_EX), question["score"], "->", question["score"] - 1,
                  session.col(Fore.RESET))
            print(session.col(Fore.GREEN) + "Correct answer: ", session.col(Style.BRIGHT), correctAnswerIndex, ". ",
                  question["correct"], session.col(Fore.RESET),
                  sep="")
            if question["score"] > -10:
                question["score"] -= 1
            session.setCardScore(question["global_index"], question["score"])
            continue

        if int(userAnswer) == correctAnswerIndex:
            print(session.col(Fore.LIGHTGREEN_EX) + "Correct!:", question["score"], "->", question["score"] + 1,
                  session.col(Fore.RESET))
            if question["score"] < 10:
                question["score"] += 1
            session.setCardScore(question["global_index"], question["score"])
            correctAnswers += 1
        else:
            print(session.col(Fore.LIGHTRED_EX) + "Incorrect!:", question["score"], "->", question["score"] - 1,
                  session.col(Fore.RESET))
            print(session.col(Fore.GREEN) + "Correct answer: ", session.col(Style.BRIGHT), correctAnswerIndex, ". ",
                  question["correct"], session.col(Fore.RESET),
                  sep="")
            if question["score"] > -10:
                question["score"] -= 1
            session.setCardScore(question["global_index"], question["score"])

    print(session.col(Fore.LIGHTYELLOW_EX) + "You answered", correctAnswers, "questions correctly out of",
          len(questions),
          "questions." + session.col(Fore.RESET)) if not quitEarly else None


if __name__ == '__main__':
    args = sys.argv[1:]
    session = QuizSession(args)

    mainLoop(session)

    session.saveSet()
