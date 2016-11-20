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
        self.isBuy = True if isBuy == 'B' else False
        self.shares = int(shares)
        self.price = float(price)

# possibleTrades are all the trades that could be conducted in order of most profitable
# currentTrades are all the trades that are associated with this order
class Position:
    def addNewTrade(self, trade):
        valuePerShare = trade.price - self.price
        sharesToPurchase = 0
        sharesRemaining = self.countSharesRemaining()

        # Greedily fill the position
        if (sharesRemaining != 0):

            sharesToPurchase = trade.shares if trade.shares >= sharesRemaining else sharesRemaining
            

        # Remove the old, worse shares if we are able to
        # currentTrades is sorted lowest price first
        # so the first trade is probably the worst sale
        # Greedily add as many shares at the better price as possible
        for (curTrade in self.currentTrades):
            oldValuePerShare = curTrade.price - self.price
            if (valuePerShare > oldValuePerShare):
                sharesToOffset = curTrade.shares if curTrade.shares <= trade.shares else trade.shares 
                
                # Remove the shares purchased by the new trade
                # Remove if the trade is no longer needed
                curTrade.shares -= sharesToOffset
                if (curTrade.shares == 0):
                    self.currentTrades.remove(curTrade)

                sharesToPurchase += sharesToOffset

        # Place the new trade in the trades array
        self.currentTrade.append(Trade(trade.time, False, sharesToPurchase, trade.price))

        # Sort the trades array
        sorted(self.currentTrades, key=lambda x: x.price)


    def calcValue(self):
        cost = self.shares - self.price
        val = 0
        for trade in self.currentTrades:
            val = trade.shares * trade.price

        self.value = val - cost

    def countSharesRemaining(self):
        numShares = 0
        for trade in self.currentTrades:
            numShares += trade.shares

        return self.shares - numShares


    def __init__(self, time, isLong, shares, price):
        self.time = float(time)
        self.isLong = isLong
        self.shares = int(shares)
        self.price = float(price)
        self.value = 0
        self.currentTrades = []



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
                                    struct.unpack('<i', f.read(4))[0],
                                    struct.unpack('<i', f.read(4))[0],
                                    struct.unpack('<i', f.read(4))[0])

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
            dayms = (time_struct.tm_hour-5) * 60 * 60 + time_struct.tm_min * 60 + time_struct.tm_sec;
            dayms *= 1000

            newTrade = Trade(dayms, tokens[1], tokens[2], tokens[3]) 
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
        if (spread >= 1): 
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





# TODO check if it will alter the quotes or trades objects
# TODO binary insert instead of resorting entire array
# TODO make sure I am not missing bids or asks in this logic
#       This could happen if I only use the trade index, maybe
def calcValidTrades(quotes, trades):
    # quoteIndex is used to iterate over the quotes
    # openBids and openAsks stores the buys and sells that haven't been filled
    # completedTrades stores the trades that were made successfully
    quoteIndex = 0
    openBids = []
    openAsks = []
    completedTrades = [];

    # Iterate over the trades
    for trade in trades: 

        # Get the current quote bid and ask
        # If the quote timestamp is less than the trade timestamp,
        # then the trade order has been placed, so add it to the appropriate array
        quote = quotes[quoteIndex]
        if (quote.time > trade.time):
            if (trade.isBuy):
                openBids.append(trade)
            else:
                openAsks.append(trade)

            # Sort the arrays on price first, then on time
            # This will ensure that the lowest gets served first
            # TODO is this what I want???
            # Need to figure out if we want to sort it like this
            # Are they served in the order received?
            sorted(openBids, key=lambda x: (-x.price, x.time))
            sorted(openAsks, key=lambda x: (x.price, x.time))

        defaultBid = Trade(0, True, 0, 0)
        defaultAsk = Trade(0, False, 0, sys.maxint) 
        highBid = openBids[0] if len(openBids) else defaultBid
        lowAsk = openAsks[0] if len(openAsks) else defaultAsk
        while (quote.time < trade.time):
            # Only iterate to a new quote if there are no orders to fill
            if ((quote.askPrice > highBid.price or quote.askShares == 0) 
                    and (quote.bidPrice < lowAsk.price or quote.bidShares == 0)):
                quoteIndex += 1
                quote = quotes[quoteIndex]

            if (quote.askPrice < highBid.price):
                # Can fill the order fully
                if (quote.askShares > highBid.shares):
                    completedTrades.append(Trade(quote.time, True, highBid.shares, quote.askPrice))
                    openBids.pop(0)
                    highBid = openBids[0] if len(openBids) else defaultBid
                    quote.askShares -= highBid.shares
                # Can fill the order partially
                else:
                    completedTrades.append(Trade(quote.time, True, quote.askShares, quote.askPrice))
                    highBid.shares -= quote.askShares
                    quote.askShares = 0

            if (quote.bidPrice > lowAsk.price):
                # Can fill the order fully
                if (quote.bidShares > lowAsk.shares):
                    completedTrades.append(Trade(quote.time, False, lowAsk.shares, quote.bidPrice))
                    openAsks.pop(0)
                    lowAsk = openAsks[0] if len(openAsks) else defaultAsk
                    quote.bidShares -= highBid.shares
                # Can fill the order partially
                else:
                    completedTrades.append(Trade(quote.time, False, quote.bidShares, quote.bidPrice))
                    lowAsk.shares -= quote.bidShares
                    quote.bidShares = 0

    # print len(completedTrades)
    # print len(trades)
            


# If the trade is valid (trade price is below bid if buy or above ask if sell)
# then buy it (or sell it I guess). Only buy or sell to the amount in the quote
# Create a position for it
# then for the next minute, add trades to possible trades in the position object

# When a position is "open" 
def maxDealer(quotes, trades):




# TODO Could speed up by generators on the quotes and trades
def main():
    quotes = readQuotes()
    trades = readTrades()
    # print "Percent of time locked or crossed: %.3f%%" % calcLockCrossTime(quotes)
    # plotSpreadHist(quotes)
    # calcValidTrades(quotes, trades)
    maxDealer(quotes, trades)


if __name__ == "__main__":
    main()
