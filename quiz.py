import json
import random
import time
import sys

from inspect import currentframe
from colorama import Fore, Back, Style


def getLine():
    cf = currentframe()
    return cf.f_back.f_lineno


class QuizSession:
    def __init__(self, args: list):
        self.loadedFile = ""
        self.lengths = []
        self.loadedData = {}
        self.questions = []

        self.debug = False
        self.colorize = True

        parsed = self.parseArgs(args)
        interpreted = self.interpretArgs(parsed)

        start = time.time()
        # extra argument handling
        if "file" in interpreted:
            if "toClear" in interpreted:
                print(self.col(Fore.YELLOW) + "Clearing scores from", interpreted["file"] + self.col(Fore.RESET))
                self.loadSet(interpreted["file"])
                for pool in self.loadedData:
                    for card in pool["cards"]:
                        card["score"] = 0
                self.saveSet(interpreted["file"])
                print(self.col(Fore.GREEN) + "Done!" + self.col(Fore.RESET))
                quit(0)
            file = interpreted["file"]
            numRandom = interpreted["numCards"] if "numCards" in interpreted else 20
        elif "dir" in interpreted:
            dirName = interpreted["dir"]
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
        self.debugPrint("Loading", file, "with", numRandom, "random cards", getLine())
        print(self.col(Fore.CYAN), "=========>", file[:-5], f"({numRandom} questions)", "<=========")
        self.loadedFile = file
        self.loadSet(file)

        # pick random cards
        randomCards = self.getCardsRandom(numRandom)
        self.questions = self.getQuestions(randomCards)
        self.debugPrint(self.questions, getLine())

        end = time.time()
        self.debugPrint("Preparation done in", end - start, "ms.", getLine())

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
                self.lengths.append(pool["length"])

            self.debugPrint("Loaded", len(pools), "quiz pools with", sum(self.lengths), "cards total", getLine())
            self.debugPrint("Lengths:", self.lengths, getLine())

    def saveSet(self) -> None:
        with open(self.loadedFile, "w", encoding='utf8') as opened:
            toSave = {
                "pools": self.loadedData
            }
            json.dump(toSave, opened, ensure_ascii=False)

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
        # debugPrint(pool_index, index, all_cards, getLine())

        card = self.loadedData[pool_index]["cards"][index - all_cards]
        card["pool_id"] = pool_index
        card["global_index"] = index

        return card

    def setCardScore(self, index: int, score: int) -> None:
        card = self.getCard(index)
        self.debugPrint(card, getLine())
        localIndex = card["global_index"] - sum(self.lengths[:card["pool_id"]])
        self.debugPrint(localIndex, getLine())
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
                scores.append(1 + ((10 - (card["score"] + 5)) * 0.9))
        weights = [score / sum(scores) for score in scores]
        self.debugPrint("Weights:", weights, getLine())
        self.debugPrint("Indices:", indices, getLine())
        randomIndices = random.choices(indices, weights=weights, k=num)
        self.debugPrint("Random Indices:", randomIndices, getLine())
        for index in randomIndices:
            cards.append(self.getCard(index))

        return cards

    def getCardsRandomFromPool(self, pool: int, num: int) -> list:
        return random.choices(self.loadedData[pool]["cards"], k=num)

    def getQuestions(self, cards: list) -> list:
        questionsToReturn = []
        for card in cards:
            poolId = card["pool_id"]
            randomInPool = self.getCardsRandomFromPool(poolId, 3)
            answers = [card["side2"]] + [cardRandom["side2"] for cardRandom in randomInPool]
            random.shuffle(answers)
            question = {
                "question": card["side1"],
                "answers": answers,
                "correct": card["side2"],
                "global_index": card["global_index"],
                "score": card["score"]
            }
            questionsToReturn.append(question)

        return questionsToReturn

    def parseArgs(self, args: list) -> list[list[str]]:
        self.debug = "--debug" in args or "-d" in args if len(sys.argv) > 1 else False
        self.debugPrint("Debug mode enabled!", getLine())
        self.debugPrint("Raw Arguments:", args, getLine())

        parsedArgs = []
        for arg in args:
            if arg.startswith("-"):
                parsedArgs.append([arg])
            else:
                parsedArgs[-1].append(arg)

        self.debugPrint("Parsed Arguments:", parsedArgs, getLine())
        return parsedArgs

    def interpretArgs(self, args: list[list[str]]) -> dict[str, str]:
        interpreted = {}
        for argGroup in args:
            if argGroup[0] == "--debug" or argGroup[0] == "-d":
                continue
            elif argGroup[0] == "--clear" or argGroup[0] == "-c":
                interpreted["toClear"] = True
            elif argGroup[0] == "--help" or argGroup[0] == "-h":
                print("Usage: python quiz.py [options]")
                print("Options:")
                print("  --help, -h: Display this help message.")
                print("  --debug, -d: Enable debug mode.")
                print("  --clear, -c: Clear all scores from the file specified in --file. If --file is not specified, "
                      "the program will exit.")
                print("  --file, -f: Load a specific file from a path.")
                print("  --dir, -D: Set a specific root directory to load files from. If --file is also specified, "
                      "this will be ignored.")
                print("  --num-cards, -n: Load a specific number of cards, default is 20.")
                print("  --no-colorize, -N: Disable colorization.")
                quit(0)
            elif argGroup[0] == "--dir" or argGroup[0] == "-D":
                if len(argGroup) < 2:
                    print("FATAL: No directory name provided to load!")
                    quit(1)

                if not argGroup[1].endswith("/"):
                    argGroup[1] += "/"

                dirName = argGroup[1]
                interpreted["dir"] = dirName
            elif argGroup[0] == "--file" or argGroup[0] == "-f":
                if len(argGroup) < 2:
                    print("FATAL: No file name provided to load!")
                    quit(1)

                if not argGroup[1].endswith(".json"):
                    print("FATAL: File name provided is not a .json file!")
                    quit(1)

                fileName = argGroup[1]
                interpreted["file"] = fileName

            elif argGroup[0] == "--num-cards" or argGroup[0] == "-n":
                if len(argGroup) < 2:
                    print("FATAL: No file name provided to load!")
                    quit(1)

                try:
                    numCards = int(argGroup[1])
                except ValueError:
                    print("FATAL: Number of cards provided is not an integer!")
                    quit(1)

                interpreted["numCards"] = numCards

            elif argGroup[0] == "--no-colorize" or argGroup[0] == "-N":
                interpreted["noColorize"] = True
                self.colorize = False
            else:
                print("WARNING: Unknown argument:", argGroup[0], "Continuing...")
                continue

        return interpreted


def mainLoop(session: QuizSession, questions: list) -> None:
    correctAnswers = 0
    quitEarly = False
    for num, question in enumerate(questions):
        print(session.col(Fore.CYAN), num + 1, "/", len(questions), ". ", session.col(Fore.GREEN),
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
            print(session.col(Fore.GREEN) + "Correct answer: ", session.col(Style.BRIGHT), correctAnswerIndex, ". ",
                  question["correct"], session.col(Fore.RESET),
                  sep="")
            question["score"] -= 1
            session.setCardScore(question["global_index"], question["score"])
            continue

        if int(userAnswer) == correctAnswerIndex:
            print(session.col(Fore.LIGHTGREEN_EX) + "Correct!:", question["score"], "->", question["score"] + 1,
                  session.col(Fore.RESET))
            question["score"] += 1
            session.setCardScore(question["global_index"], question["score"])
            correctAnswers += 1
        else:
            print(session.col(Fore.LIGHTRED_EX) + "Incorrect!:", question["score"], "->", question["score"] - 1,
                  session.col(Fore.RESET))
            print(session.col(Fore.GREEN) + "Correct answer: ", session.col(Style.BRIGHT), correctAnswerIndex, ". ",
                  question["correct"], session.col(Fore.RESET),
                  sep="")
            question["score"] -= 1
            session.setCardScore(question["global_index"], question["score"])

    print(session.col(Fore.LIGHTYELLOW_EX) + "You answered", correctAnswers, "questions correctly out of",
          len(questions),
          "questions." + session.col(Fore.RESET)) if not quitEarly else None


if __name__ == '__main__':
    args = sys.argv[1:]
    session = QuizSession(args)

    questions = session.getLoadedQuestions()

    mainLoop(session, questions)

    session.saveSet()
