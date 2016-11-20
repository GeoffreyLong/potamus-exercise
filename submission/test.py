import unittest
import answers
import struct
import random

class TestAnswers(unittest.TestCase):
    # Could use setUpClass and tearDownClass
    #   @classmethod
    #   def setUpClass(cls):
    #       # Get slow stuff

    def setUp(self):
        self.createQuotes("testQuotes.txt", "testQuotes.data");
        self.createTrades("testTrades.txt", "testTradesProc.txt");
        
        self.quotes = answers.readQuotes("testQuotes.data");
        self.trades = answers.readTrades("testTradesProc.txt");
        self.allTimes = sorted(self.quotes + self.trades, key=lambda x: (x.time, isinstance(x, answers.Trade)))

    def tearDown(self):
        self.quotes = None
        self.trades = None
        self.allTimes = None

    def createQuotes(self, readFile, writeFile):
        quoteData = []
        with open(readFile, 'r') as f:
            line = f.readline()
            while line:
                tokens = line.rstrip('\n').split()
                quoteData.extend(tokens)
                line = f.readline()


        with open(writeFile, 'wb') as f:
            for quote in quoteData:
                f.write(struct.pack('<i', int(quote)))

    def createTrades(self, readFile, writeFile):
        baseTime = 1365134400
        tradeData = []
        with open(readFile, 'r') as f:
            line = f.readline()
            while line:
                tokens = line.rstrip('\n').split()
                tokens[0] = int(tokens[0]) / 1000 + baseTime
                tradeData.extend(tokens)
                line = f.readline()


        with open(writeFile, 'wb') as f:
            for i in range(0, len(tradeData)):
                f.write(str(tradeData[i]))
                if i % 4 == 3:
                    f.write('\n')
                else:
                    f.write(" ")


    def test_quotes_length(self):
        self.assertEqual(len(self.quotes), 15)
    def test_trades_length(self):
        self.assertEqual(len(self.trades), 12)


    # The lock cross time is
    #   locked between 34100000 and 34101000
    #   locked or crossed between 34110000 and 34150000
    #   total lock/cross is 41000
    #   total time is 400000
    def test_q2_time(self):
        lockCrossTime = answers.calcLockCrossTime(self.quotes)
        self.assertEqual(lockCrossTime, 41000)
    def test_q2_percent(self):
        lockCrossPercent = answers.calcLockCrossPercentage(self.quotes)
        self.assertEqual(lockCrossPercent, (41000.0 / 400000.0) * 100)
        

    def test_q3(self):
        spreads = answers.getSpreadHist(self.quotes)
        self.assertEqual(spreads, [1, 2, 3, 4, 5, 9, 18, 27, 36, 45])


    # TODO
    #       If I add 34400000 B 20000 100.50
    #       This will buy 200 shares of stock at two different times
    #       This is counted as two different trades... is this valid?
    #       Do I only want to print the trades that executed fully?
    #       Do I want to count trades that are split only once?
    # Trades 3 and 4 will not execute
    # But trade 9 and 10 will be split over two trades
    def test_q4_length(self):
        trades = answers.calcValidTrades(self.allTimes)
        self.assertEqual(len(trades), 12)

    # Will test to see if any trades are made during a crossed or locked market
    def test_q4_crossed_locked(self):
        lockedCross = [34100000, 34110000, 34120000, 34130000, 34140000]
        isLockedCross = False
        trades = answers.calcValidTrades(self.allTimes)
        for trade in trades:
            if (trade.time in lockedCross):
                isLockedCross = True
                break

        self.assertFalse(isLockedCross)
        
    # Test all the trades made
    def test_q4_trades(self):
        # The order of these trades is deterministic
        expectedTrades = [
                [34101000, False, 100, 100.00],
                [34101000, True, 100, 100.01],
                [34102000, False, 100, 100.00],
                [34102000, True, 100, 100.02],
                [34103000, False, 100, 100.00],
                [34150000, False, 50, 100.01],
                [34150000, True, 100, 100.10],
                [34150000, False, 50, 100.01],
                [34200000, True, 50, 100.20],
                [34200000, False, 50, 100.02],
                [34210000, False, 10, 100.02],
                [34210000, True, 10, 100.20]
        ]


        trades = answers.calcValidTrades(self.allTimes)
        for i in range(0, len(trades)):
            self.assertEqual(trades[i].time, expectedTrades[i][0])
            self.assertEqual(trades[i].isBuy, expectedTrades[i][1])
            self.assertEqual(trades[i].shares, expectedTrades[i][2])
            self.assertEqual(trades[i].price / 100, expectedTrades[i][3])


    # Tests to see that only valid positions are opened
    def test_q5_initialPositions(self):
        # The order of these positions is deterministic
        # I assumed that the trades were made at the current bid/ask price, not trade price
        # I also assume that quotes used for trades are also used for closing the position
        #   This means that if a quote has 100 shares and a position is opened for 100 shares, 
        #   then positions cannot be closed with it
        expectedPositions = [
                [34101000, True, 100, 100.00],
                [34101000, False, 100, 100.01],
                [34150000, True, 50, 100.01],
                [34150000, False, 100, 100.10],
                [34150000, True, 50, 100.01],
                [34210000, True, 10, 100.02],
                [34210000, False, 10, 100.20],
        ];
        positions = answers.optTrader(self.allTimes)

        for i in range(0, len(positions)):
            self.assertEqual(positions[i].time, expectedPositions[i][0])
            self.assertEqual(positions[i].isLong, expectedPositions[i][1])
            self.assertEqual(positions[i].shares, expectedPositions[i][2])
            self.assertEqual(positions[i].price / 100, expectedPositions[i][3])


    def test_q5_trades(self):
        # Note that if a trade is bought then sold to the same quote, 
        #   I don't assume this to impact the share count (the shares is not "replenished")
        #   This can be seen in the quote timestamp 3420000 and trades on 34210000
        expectedCloses = [
                [34105000, False, 100, 100.05],
                [34102000, True, 100, 100.00],
                [34200000, False, 30, 100.20],
                [34200000, True, 80, 100.02],
                [34200000, False, 50, 100.20],
                [34210000, False, 10, 100.20],
                [34210000, True, 10, 100.02]
        ];
        positions = answers.optTrader(self.allTimes)

        i = 0
        for position in positions:
            #print "Opened: %i, %i, %.2f, %s" % (position.time, position.shares, position.price / 100.0, position.isLong)
            for trade in position.trades:
                self.assertEqual(trade.time, expectedCloses[i][0])
                self.assertEqual(trade.isBuy, expectedCloses[i][1])
                self.assertEqual(trade.shares, expectedCloses[i][2])
                self.assertEqual(trade.price / 100, expectedCloses[i][3])
                
                i += 1

    # Max Exposure calculation
    #   34101000 -> 10000 + 10001 = 20001
    #   34150000 -> 50 * 100.01 + 100 * 100.10 + 50 * 100.01 = 20011
    #   34200000 -> 20011 - 30 * 100.20 - 80 * 100.02 - 50 * 100.20 = 3993.4
    #   34210000 -> 3993.4 + 10 * 100.20 + 10 * 100.02 = 5995.6
    # Max exposure by this is then 20011
    # This calculates the max profit and exposure from my algorithm, not necessarily the optimal
    # Note that the maxProfit is negative since we cannot sell all the trades given the quotes
    def test_q5_maxProfitAndExposure(self):
        positions = answers.optTrader(self.allTimes)
        results = answers.calcMaxExposureAndProfit(positions)
        self.assertEqual(results["maxProfit"], -3969.20)
        self.assertEqual(results["maxExposure"], 20011) 


    # Test that q5's solution is actually the most optimal
    # Most optimal is as follows
    #       Open:   [34101000, True, 100, 100.00],
    #       Close:  [34105000, False, 100, 100.05],
    #       Open:   [34101000, False, 100, 100.01],
    #       Close:  [34102000, True, 100, 100.00],
    #       Open:   [34150000, True, 50, 100.01],
    #       Close:  [34200000, False, 50, 100.20],
    #       Open:   [34150000, False, 100, 100.10],
    #       Close:  [34200000, True, 80, 100.20],
    #       Open:   [34150000, True, 50, 100.01],
    #       Close:  [34200000, False, 30, 100.20],
    #       Open:   [34210000, True, 10, 100.02],
    #       Close:  [34210000, False, 10, 100.20],
    #       Open:   [34210000, False, 10, 100.20],
    #       Close:  [34210000, True, 10, 100.20],
    # This is actually what I got.
    # Would need to come up with a new set of trades and quotes to more fully eval 
    #       Include trades that can only open with one quote (with others that can have same)
    #       Include quotes that have multiple different positions on them
    #       Include a position that has favorable quotes right after one with unfavorable 
    #           Do not provide enough good quotes to be shared (and vice versa)
    #def test_q5_optimal(self):
    #    self.fail()


if __name__ == '__main__':
    unittest.main()

