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
        """
        Initializes a quiz session.
        :param args: Command line arguments. See :interpretArgs() for more information.
        """
        self.loadedFile = ""
        self.loadedData = []
        self.questions = []
        self.settings = {}

        self.debug = False
        self.colorize = True

        parsed = self.parseArgs(args)
        interpreted = self.interpretArgs(parsed)
        self.settings = interpreted

        start = time.time()
        # Extra argument handling

        # Load selected file
        if "file" in interpreted:
            # Clear score data
            if "toClear" in interpreted:
                print(self.col(Fore.YELLOW) + "Clearing scores from", interpreted["file"] + self.col(Fore.RESET))
                self.loadSet(interpreted["file"])
                for card in self.loadedData: # card in cards
                    card["score"] = 0
                self.saveSet(interpreted["file"])
                print(self.col(Fore.GREEN) + "Done!" + self.col(Fore.RESET))
                quit(0)
            file = interpreted["file"]
            questionAmount = interpreted["numCards"] if "numCards" in interpreted else 20

        # Change path
        # If dir command exists
        elif "dir" in interpreted:
            dirName = interpreted["dir"]
            files = [[dirName + "N5.json", 20], [dirName + "N4.json", 10], [dirName + "N3.json", 5]]
            fileWeights = [0.5, 0.25, 0.125]

            result = random.choices(files, weights=fileWeights, k=1)[0]
            file = result[0]
            questionAmount = result[1]

        # Else, normally pathing
        else:
            files = [["N5.json", 20], ["N4.json", 10], ["N3.json", 5]]
            fileWeights = [0.5, 0.25, 0.125]

            result = random.choices(files, weights=fileWeights, k=1)[0]
            file = result[0]
            questionAmount = result[1]

        # Load the json file
        self.debugPrint("Loading", file, "with", questionAmount, "random cards", getLine())
        print(self.col(Fore.CYAN), "=========>", file[:-5], f"({questionAmount} questions)", "<=========")
        self.loadedFile = file
        self.loadSet(file)

        # Pick random cards
        randomCards = self.getCardsRandom(questionAmount)
        self.questions = self.getQuestions(randomCards)
        self.debugPrint(self.questions, getLine())

        end = time.time()
        self.debugPrint("Preparation done in", end - start, "ms.", getLine())

    # Give the command line color
    def col(self, code: str) -> str:
        return code if self.colorize else ""

    # Print but debugging
    def debugPrint(self, *args) -> None:
        if self.debug:
            print(f"{self.col(Fore.RED)}[quiz.py:{args[-1]}]{self.col(Fore.YELLOW)}", *args[:-1],
                  self.col(Style.RESET_ALL))

    # Load file, save at self.loadedData
    def loadSet(self, target: str) -> None:
        with open(target, encoding='utf8') as f:
            data = json.load(f)
            cards: list = data["cards"]
            self.loadedData = cards

            self.debugPrint("Loaded", cards.__len__(), "cards total", getLine())

    # Not saving score
    def saveSet(self, target=None) -> None:
        if "dryRun" in self.settings and "toClear" not in self.settings:
            print(self.col(Fore.YELLOW) + "Dry run enabled, not saving!" + self.col(Fore.RESET))
            return

        if target is None:
            target = self.loadedFile

        with open(target, "w", encoding='utf8') as opened:
            toSave = {
                "cards": self.loadedData
            }
            json.dump(toSave, opened, ensure_ascii=False, indent=4)

    # Get card from index in cards aka self.loadedData
    def getCard(self, Index: int) -> dict:
        # Get card.dictionary
        card = self.loadedData[Index]
        # Add index key
        return {
            "word": card["word"],
            "meaning": card["meaning"],
            "score": card["score"],
            "index": Index
        }

    # Set card a new score!
    def setCardScore(self, Index: int, score: int) -> None:
        self.loadedData[Index]["score"] = score

    # Randomly choose the cards
    def getCardsRandom(self, questionAmount: int) -> list:
        # Choose cards by weighted scores
        indices = []
        # Score = [-10,10] in math
        scores = []
        cards = []
        for index, card in enumerate(self.loadedData):
            indices.append(index)
            if "reverseWeights" in self.settings:
                scores.append(card["score"]*-1 + 0.1)
            else:
                scores.append(card["score"] + 0.1)
        sum_scores = sum(scores)
        self.debugPrint("sum scores:", sum_scores, getLine())
        weights = [(score / sum_scores) * 100 for score in scores]
        del sum_scores
        self.debugPrint("Scores:", scores, getLine())
        self.debugPrint("Weights:", weights, getLine())
        self.debugPrint("Indices:", indices, getLine())
        randomIndices = random.choices(indices, weights=weights, k=questionAmount)
        self.debugPrint("Random Indices:", randomIndices, getLine())
        for index in randomIndices:
            cards.append(self.getCard(index))

        return cards

    # Random fake answers / wrong answers
    def getRandomCards(self, num: int, excludesIndex: int = None) -> list:
        cards = self.loadedData.copy()
        if excludesIndex is not None:
            cards.pop(excludesIndex)

        return random.choices(cards, k=num)

    def getQuestions(self, cards: list) -> list:
        questionsToReturn = []
        for card in cards:
            wrongCards = self.getRandomCards(3, card["index"])
            meaningCard = random.choice(card["meaning"])
            answers = [meaningCard] + [random.choice(cardRandom["meaning"]) for cardRandom in wrongCards]
            random.shuffle(answers)
            question = {
                "question": card["word"],
                "answers": answers,
                "correct": meaningCard,
                "index": card["index"],
                "score": card["score"]
            }
            questionsToReturn.append(question)

        return questionsToReturn

    # Command prompt/ Terminal args
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

            elif argGroup[0] == "--dry-run":
                interpreted["dryRun"] = True

            elif argGroup[0] == "--reverse-weights" or argGroup[0] == "-r":
                interpreted["reverseWeights"] = True
            else:
                print("WARNING: Unknown argument:", argGroup[0], "Continuing...")
                continue

        return interpreted


def mainLoop(session: QuizSession) -> None:
    questions = session.questions

    correctAnswers = 0
    quitEarly = False
    totalTime = 0
    print(session.col(Fore.LIGHTGREEN_EX) + "Ready..." + session.col(Fore.RESET))
    time.sleep(1)
    print(session.col(Fore.LIGHTYELLOW_EX) + "Set.." + session.col(Fore.RESET))
    time.sleep(1)
    print(session.col(Fore.LIGHTRED_EX) + "GO!" + session.col(Fore.RESET))
    time.sleep(1)
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
        timeBonus = time.perf_counter()
        while not isValid:
            userAnswer = input(session.col(Fore.CYAN) + "Answer (1-4, n for don't know): " + session.col(Fore.RESET))
            isValid = userAnswer == "q" or userAnswer == "n" or (userAnswer.isdigit() and 1 <= int(userAnswer) <= 4)
            print(session.col(Fore.RED) + "Invalid input!" + session.col(Fore.RESET)) if not isValid else None;
        timeBonus = time.perf_counter() - timeBonus
        print(session.col(Fore.LIGHTYELLOW_EX) + "You used", timeBonus, "second(s)" + session.col(Fore.RESET))
        totalTime += timeBonus
        if timeBonus > 10:
            timeBonus = 1
        elif timeBonus < 6:
            timeBonus = 2
        else:
            timeBonus = (16-timeBonus)/5
        if userAnswer == "q":
            print(session.col(Fore.RED) + "You quit early!" + session.col(Fore.RESET))
            print(session.col(Fore.LIGHTYELLOW_EX) + "You used a total of", totalTime, "second(s) to answered", correctAnswers
          , "questions correctly out of",num,"questions." + session.col(Fore.RESET))
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
            session.setCardScore(question["index"], question["score"])
            continue

        if int(userAnswer) == correctAnswerIndex:
            print(session.col(Fore.LIGHTGREEN_EX) + "Correct!:", question["score"], "->", question["score"] + timeBonus,
                  session.col(Fore.RESET))
            if question["score"] < 10:
                question["score"] += timeBonus
            session.setCardScore(question["index"], question["score"])
            correctAnswers += 1
        else:
            print(session.col(Fore.LIGHTRED_EX) + "Incorrect!:", question["score"], "->", question["score"] - timeBonus,
                  session.col(Fore.RESET))
            print(session.col(Fore.GREEN) + "Correct answer: ", session.col(Style.BRIGHT), correctAnswerIndex, ". ",
                  question["correct"], session.col(Fore.RESET),
                  sep="")
            if question["score"] > -10:
                question["score"] -= timeBonus
            session.setCardScore(question["index"], question["score"])
    print(session.col(Fore.LIGHTYELLOW_EX) + "You used a total of", totalTime, "second(s) to answered", correctAnswers
          , "questions correctly out of",len(questions),"questions." + session.col(Fore.RESET)) if not quitEarly else None


if __name__ == '__main__':
    args = sys.argv[1:]
    session = QuizSession(args)

    mainLoop(session)

    session.saveSet()
