import struct
import sys
import matplotlib.pyplot as plt
import numpy as np
import time

class Quote:
    def __init__(self, time, askShare, askPrice, bidShare, bidPrice):
        self.time = float(time)
        self.askShares = int(askShare)
        self.askPrice = float(askPrice)
        self.bidShares = int(bidShare)
        self.bidPrice = float(bidPrice)

class Trade:
    def __init__(self, time, isBuy, shares, price):
        self.time = float(time)
        self.isBuy = isBuy
        self.shares = int(shares)
        self.price = float(price)


class Position:
    # This version assumes I can trade arbitrary numbers of stocks at the quote price
    # I am not checking whether or not the number of quote shares allows it
    # I am also not considering selling to trades that are buying or vice versa
    def checkTrade(self, quote):
        # Can trade by crossing the spread
        # So we can buy at the bid and sell at the ask price

        profitPerShare = 0
        if (self.isLong and quote.bidShares != 0):
            shares = 0
            if (self.sharesRemaining):
                shares = self.sharesRemaining if self.sharesRemaining <= quote.bidShares else quote.bidShares
                self.sharesRemaining -= shares
            else:
                profitPerShare = self.price - quote.bidPrice
                for trade in trades:
                    tradeProfitPerShare = self.price - trade.price
                    if (profitPerShare > tradeProfitPerShare and quote.bidShares > 0):
                        tradeShares = quote.bidShares if trade.shares < quote.bidShares else trade.shares
                        trade.shares -= tradeShares
                        quote.bidShares -= tradeShares
                        shares += tradeShares

            self.trades.append(Trade(quote.time, False, shares, quote.bidPrice))

        elif (not self.isLong and quote.askShares != 0):
            shares = 0
            if (self.sharesRemaining):
                shares = self.sharesRemaining if self.sharesRemaining <= quote.askShares else quote.askShares
                self.sharesRemaining -= shares

            else:
                profitPerShare = quote.askPrice - self.price
                for trade in trades:
                    tradeProfitPerShare = trade.price - self.price
                    if (profitPerShare > tradeProfitPerShare and quote.askShares > 0):
                        tradeShares = quote.askShares if trade.shares < quote.askShares else trade.shares
                        trade.shares -= tradeShares
                        quote.askShares -= tradeShares
                        shares += tradeShares

            self.trades.append(Trade(quote.time, True, shares, quote.askPrice))



    def __init__(self, time, isLong, shares, price):
        self.time = float(time)
        # If the trade we are filling is a buy, then we are selling shares so short
        self.isLong = isLong
        self.shares = int(shares)
        self.sharesRemaining = int(shares)
        self.price = float(price)
        self.trades = [] 
        self.profitPerShare = -price



def readQuotes():
    quotes = []
    with open("aapl.data", "rb") as f:
        word = f.read(4)
        while word:
            # Add each 3 pm tuesday fieldbook challenging tech problem
            # solve algorithmic problem

            # Add a datapoint for each quote
            try: 
                newTime = Quote(struct.unpack('<i', word)[0],
                                    struct.unpack('<i', f.read(4))[0],
                                    float(struct.unpack('<i', f.read(4))[0]) / 100,
                                    struct.unpack('<i', f.read(4))[0],
                                    float(struct.unpack('<i', f.read(4))[0]) / 100)

                #TODO will yield a few with -1 as ask
                quotes.append(newTime)
                # Print data for testing
                # print tuple(vars(newTime))
                # print "%d, %d, %d, %d, %d" % tuple(vars(newTime)[a] for a in vars(newTime))
            except:
                #TODO for some reason the last data point isn't being read in
                print "Unable to parse data point for time: %d" % struct.unpack('<i', word)[0]
                print sys.exc_info()

            word = f.read(4)

    f.close()
    return quotes

def readTrades():
    trades = []
    with open("trades.txt", "r") as f:
        line = f.readline()
        while line:
            tokens = line.rstrip('\n').split()
            time_struct = time.gmtime(float(tokens[0]))
            dayms = (time_struct.tm_hour-4) * 60 * 60 + time_struct.tm_min * 60 + time_struct.tm_sec;
            dayms *= 1000

            newTrade = Trade(dayms, True if tokens[1] == 'B' else False, tokens[2], tokens[3]) 
            trades.append(newTrade)

            line = f.readline()

    return trades


def calcLockCrossTime(quotes):
    lockCrossTime = 0

    # Set the flag and last time of the initial quote
    isLockCross = (quotes[0].bidPrice >= quotes[0].askPrice)
    lastTime = quotes[0].time

    # Iterate over all the quotes, 
    # skipping the first
    for i in range(1, len(quotes)):
        quote = quotes[i]

        # Get the time elapsed from the last quote
        timeDelta = quote.time - lastTime

        # If the market was locked or crossed during the last interval, 
        # then add the elapsed time to lockCrossTime
        if (isLockCross):
            lockCrossTime += timeDelta

        # Set the flag and the lastTime for the next iteration
        isLockCross = (quote.bidPrice >= quote.askPrice)
        lastTime = quote.time

    # Calculate the total time of the market
    # Convert totalTime to a float to avoid integer division
    totalTime = quotes[-1].time - quotes[0].time
    print lockCrossTime
    return (lockCrossTime / float(totalTime)) * 100

    
# Plot a histogram of the spread where the frequency is in quote occurrence 
# TODO implement a second with time and another with quotes
def plotSpreadHist(quotes):
    # Create an empty array to store the spreads
    spreads = []

    # For each quote, add the spread value if the spread is greater than 0
    for quote in quotes:
        spread = quote.askPrice - quote.bidPrice
        if (spread >= 0.01): 
            spreads.append(spread)

    # Plot and display the histogram
    showHistogram(spreads)




# This will display the histogram
def showHistogram(spreads):
    # Set the bins of the histogram and set the data
    maxVal = max(spreads)
    plt.hist(spreads, bins=[i for i in range(1,maxVal)])
    
    # Will limit the x range, but it is hard to see the initial value
    # plt.xlim(1,maxVal)

    # Set the labels of the histogram
    plt.title("Spread Histogram")
    plt.xlabel("Spread")
    plt.ylabel("Frequency")

    # Display the histogram
    plt.show()

    # This will save the plot
    # TODO test
    # fig = plt.gcf()
    # plot_url = py.plot_mpl(fig, filename='histogram')


def calcValidTradesNew(quotes, trades):
    quoteIndex = 0
    openBids = []
    openAsks = []
    completedTrades = []

    for trade in trades:
        quote = quotes[quoteIndex]
        askPrice = quote.askPrice
        bidPrice = quote.bidPrice
        while (quote.time < trade.time):
            #print "Quote: %i, %f, %f" % (quote.time, quote.bidPrice, quote.askPrice)
            askPrice = quote.askPrice
            bidPrice = quote.bidPrice

            for bid in openBids:
                if (bid.price >= askPrice):
                    completedTrades.append(Trade(quote.time, True, bid.shares, bid.price))
                    openBids.remove(bid)

            for ask in openAsks:
                if (ask.price <= bidPrice):
                    completedTrades.append(Trade(quote.time, False, ask.shares, ask.price))
                    openAsks.remove(ask)

            quoteIndex += 1
            quote = quotes[quoteIndex]

        if ((trade.isBuy and trade.price >= askPrice and askPrice > 0)
                or (not trade.isBuy and trade.price <= bidPrice)):
            completedTrades.append(Trade(trade.time, trade.isBuy, trade.shares, trade.price))
            #print "Trade: %i, %f, %s" % (trade.time, trade.price, trade.isBuy)
        else:
            trade = Trade(trade.time, trade.isBuy, trade.shares, trade.price)
            if (trade.isBuy):
                openBids.append(trade)
                sorted(openBids, key=lambda x: -x.price)
            else:
                openAsks.append(trade)
                sorted(openAsks, key=lambda x: x.price)

    print len(completedTrades)
    print len(trades)


def calcValidTrades(quotes, trades):
    quoteIndex = 0
    openBids = []
    openAsks = []
    completedTrades = []

    for trade in trades:
        quote = quotes[quoteIndex]
        askPrice = quote.askPrice
        bidPrice = quote.bidPrice
        while (quote.time < trade.time):
            #print "Quote: %i, %f, %f" % (quote.time, quote.bidPrice, quote.askPrice)
            askPrice = quote.askPrice
            bidPrice = quote.bidPrice

            if (len(openBids) and openBids[-1].price >= askPrice):
                bid = openBids.pop()
                completedTrades.append(Trade(quote.time, True, bid.shares, bid.price))
                #print "Trade: %i, %f, %s" % (quote.time, bid.price, bid.isBuy)

            elif (len(openAsks) and openAsks[0].price <= bidPrice):
                ask = openAsks.pop(0)
                completedTrades.append(Trade(quote.time, True, ask.shares, ask.price))
                #print "Trade: %i, %f, %s" % (quote.time, ask.price, ask.isBuy)

            else:
                quoteIndex += 1
                quote = quotes[quoteIndex]

        if ((trade.isBuy and trade.price >= askPrice and askPrice > 0)
                or (not trade.isBuy and trade.price <= bidPrice)):
            completedTrades.append(Trade(trade.time, trade.isBuy, trade.shares, trade.price))
            #print "Trade: %i, %f, %s" % (trade.time, trade.price, trade.isBuy)
        else:
            trade = Trade(trade.time, trade.isBuy, trade.shares, trade.price)
            if (trade.isBuy):
                insertSort(openBids, trade)
            else:
                insertSort(openAsks, trade)

    print len(completedTrades)
    print len(trades)
        
def insertSort(alist, elm):
    low = 0
    high = len(alist)

    while (low < high):
        middle = (low + high) // 2
        if (alist[middle].price < elm.price):
            low = middle + 1
        else:
            high = middle

    alist.insert(low, elm)



def optimalDealer(quotes, trades):
    quoteIndex = 0
    openPositions = []
    allPositions = []

    for trade in trades:
        quote = quotes[quoteIndex]

        askPrice = quote.askPrice
        bidPrice = quote.bidPrice
        while (quote.time < trade.time):
            askPrice = quote.askPrice
            bidPrice = quote.bidPrice

            for position in openPositions:
                # If the position was opened over a minute ago, 
                # then remove it from consideration
                if (quote.time > (position.time + 60000)):
                    openPositions.remove(position)
                    continue

                position.checkTrade(quote)


            quoteIndex += 1
            quote = quotes[quoteIndex]


        if ((trade.isBuy and trade.price >= askPrice) 
                or (not trade.isBuy and trade.price <= bidPrice)):
            position = Position(trade.time, trade.isBuy, trade.shares, trade.price)
            openPositions.append(position)
            allPositions.append(position)

    # for position in allPositions:
    #    print "Opened: %i, %i, %f, %s" % (position.time, position.shares, position.price, position.isLong)
    #    print "Closed: %i, %i, %f, %s" % (position.trade.time, position.trade.shares, position.trade.price, position.trade.isBuy)


def newCalcValidTrades(allTimes):
    openTrades = []
    validTrades = []
    lastQuote = None

    for time in allTimes:
        if (isinstance(time, Trade)):
            openTrades.append(Trade(time.time, time.isBuy, time.shares, time.price))

            
        if (isinstance(time, Quote)):
            if lastQuote is not None:
                # Don't do anything in a locked or crossed market
                if (lastQuote.askPrice <= lastQuote.bidPrice):
                    lastQuote = Quote(time.time, time.askShares, time.askPrice, time.bidShares, time.bidPrice)
                    continue

                # Slow... consider better structure for openTrades
                for trade in openTrades:
                    if (trade.shares == 0): 
                        openTrades.remove(trade)
                        continue

                    if (trade.isBuy 
                            and trade.price >= lastQuote.askPrice 
                            and lastQuote.askShares > 0):
                        # See how many shares I can buy
                        shares = trade.shares if trade.shares <= lastQuote.askShares else lastQuote.askShares
                        # Append a trade to valid trades
                        validTrades.append(Trade(lastQuote.time, True, shares, lastQuote.askPrice))

                        trade.shares -= shares
                        lastQuote.askShares -= shares
                    
                    elif (not trade.isBuy 
                            and trade.price <= lastQuote.bidPrice
                            and lastQuote.bidShares > 0):
                        # See how many shares I can buy
                        shares = trade.shares if trade.shares <= lastQuote.bidShares else lastQuote.bidShares
                        # Append a trade to valid trades
                        validTrades.append(Trade(lastQuote.time, False, shares, lastQuote.bidPrice))
                        
                        trade.shares -= shares
                        lastQuote.bidShares -= shares

            lastQuote = Quote(time.time, time.askShares, time.askPrice, time.bidShares, time.bidPrice)
            
    print len(validTrades)
    print len(openTrades)

def newOptTrader(allTimes):
    heldPositions = []
    allPositions = []
    lastQuote = None

    for time in allTimes:
        if (isinstance(time, Trade)):
            trade = time
            if (lastQuote is not None):
                shares = 0
                price = 0;
                if (trade.isBuy 
                        and trade.price >= lastQuote.askPrice 
                        and lastQuote.askShares > 0):
                    # See how many shares I can buy
                    shares = trade.shares if trade.shares <= lastQuote.askShares else lastQuote.askShares
                    lastQuote.askShares -= shares
                    price = lastQuote.askPrice
                
                elif (not trade.isBuy 
                        and trade.price <= lastQuote.bidPrice
                        and lastQuote.bidShares > 0):
                    # See how many shares I can buy
                    shares = trade.shares if trade.shares <= lastQuote.bidShares else lastQuote.bidShares
                    lastQuote.bidShares -= shares
                    price = lastQuote.bidPrice
                
                if (shares != 0):
                    position = Trade(trade.time, not trade.isBuy, shares, price))
                    heldPositions.append(position)
                    allPositions.append(position)

            
        if (isinstance(time, Quote)):
            # Can't do anything in a locked or crossed market
            if (time.askPrice <= time.bidPrice):
                continue

            quote = Quote(time.time, time.askShares, time.askPrice, time.bidShares, time.bidPrice) 
            for position in heldPositions:
                # If the position has been held for over a minute, then remove it
                if (lastQuote.time <= (position.time + 60000)):
                    heldPositions.remove(position)
                    continue

                # If there are no shares to sell or buy then break the loop
                if (quote.askShares == 0 and quote.bidShares == 0):
                    break

                
                position.checkTrade(quote)



            lastQuote = quote




# TODO Could speed up by generators on the quotes and trades
def main():
    quotes = readQuotes()
    trades = readTrades()
    # print "Percent of time locked or crossed: %.3f%%" % calcLockCrossTime(quotes)
    # plotSpreadHist(quotes)
    calcValidTrades(quotes, trades)
    # optimalDealer(quotes, trades)
    # Combine the two into a list
    allTimes = sorted(quotes + trades, key=lambda x: x.time)
    newCalcValidTrades(allTimes)


if __name__ == "__main__":
    main()
