# TODO
#   Figure out why converting the quote to float then dividing by 100
#       gives strange values in the histogram output
#       when all the other methods remain unchanged by it


# sell -> Long (own stock) -> buy (need someone to buy)
# buy -> short (sold stock) -> sell (need someone to sell us stock)



import struct
import sys
import matplotlib.pyplot as plt
import numpy as np
import time

# This is for the quote data
class Quote:
    def __init__(self, time, askShare, askPrice, bidShare, bidPrice):
        self.time = time
        self.askShares = int(askShare)
        self.askPrice = float(askPrice)
        self.bidShares = int(bidShare)
        self.bidPrice = float(bidPrice)

# This is for the trade data
class Trade:
    def __init__(self, time, isBuy, shares, price):
        self.time = int(time)
        self.isBuy = isBuy
        self.shares = int(shares)
        self.price = float(price)
        self.sharesRemaining = shares

# A position can be thought of as an opening trade which has trades to close it
# TODO
#   I could refactor the time, isLong, shares, and price into a field open of type trade
#   I could also possibly make position a subclass of trade
class Position:
    # Will greedily choose the best trade to close out the position
    def checkTrade(self, quote):
        # TODO 
        #   Refactor this so that there isn't repeated logic
        #   Pass in the quote as trades
        if (self.isLong and quote.askShares != 0):
            shares = 0
            if (self.sharesRemaining > 0):
                shares = self.sharesRemaining if self.sharesRemaining <= quote.askShares else quote.askShares
                self.sharesRemaining -= shares
                quote.askShares -= shares
            else:
                profitPerShare = quote.askPrice - self.price 
                for trade in self.trades:
                    tradeProfitPerShare = trade.price - self.price
                    if (profitPerShare > tradeProfitPerShare and quote.askShares > 0):
                        tradeShares = quote.askShares if quote.askShares < trade.shares else trade.shares
                        trade.shares -= tradeShares
                        quote.askShares -= tradeShares
                        shares += tradeShares

                        if (trade.shares == 0):
                            self.trades.remove(trade)

            if (shares > 0):
                self.trades.append(Trade(quote.time if quote.time > self.time else self.time, False, shares, quote.askPrice))
                self.calcValuePerShare()

        elif (not self.isLong and quote.bidShares != 0):
            shares = 0
            if (self.sharesRemaining > 0):
                shares = self.sharesRemaining if self.sharesRemaining <= quote.bidShares else quote.bidShares
                self.sharesRemaining -= shares
                quote.bidShares -= shares
            else:
                profitPerShare = self.price - quote.bidPrice
                for trade in self.trades:
                    tradeProfitPerShare = self.price - trade.price
                    if (profitPerShare > tradeProfitPerShare and quote.bidShares > 0):
                        tradeShares = quote.bidShares if quote.bidShares < trade.shares else trade.shares
                        trade.shares -= tradeShares
                        quote.bidShares -= tradeShares
                        shares += tradeShares

                        if (trade.shares == 0):
                            self.trades.remove(trade)

            if (shares > 0):
                self.trades.append(Trade(quote.time if quote.time > self.time else self.time, True, shares, quote.bidPrice))
                self.calcValuePerShare()
        
    def calcValuePerShare(self):
        # Get the value of the total investment
        value = self.calcValue();
        # Divide by the number of shares to get a per share value
        self.valuePerShare = value / self.shares

    def calcValue(self):
        # Tally up the value of the traded shares, 
        curValue = 0
        for trade in self.trades:
            curValue += trade.shares * trade.price

        # If it is long, then the value is the current - purchased, 
        # If it is short, then we do the opposite
        if (self.isLong):
            curValue = curValue - self.initialCost
        else:
            curValue = self.initialCost - curValue

        # Subtract everything that is not recouped (penalty for not being out of position)
        curValue -= self.sharesRemaining * self.price

        return curValue


    # sell -> Long (own stock) -> buy (need someone to buy)
    # buy -> short (sold stock) -> sell (need someone to sell us stock)
    # Greedily fill the position if there are shares remaining
    # Once the position has been filled, add the remaining trades to possible trades
    def greedyAdd(self, trade):
        if self.sharesRemaining != 0 and trade.shares != 0:
            shares = trade.shares if trade.shares < self.shares else self.shares 
            if self.isLong:
                insertSort(self.trades, 
                            Trade(trade.time, trade.isBuy, shares, trade.price)),
                            key:lambda v: v.price)
            else:
                insertSort(self.trades, 
                            Trade(trade.time, trade.isBuy, shares, trade.price)),
                            key:lambda v: -v.price)

            self.sharesRemaining -= shares

        else:
            if self.isLong:
                # Buy at the lowest possible price
                insertSort(self.possibleTrades, trade, key=lambda v: v.price)
            else:
                # Sell at the highest possible price
                insertSort(self.possibleTrades, trade, key=lambda v: -v.price)
                


    def optimize(self):
        return 0
        


    def __init__(self, time, isLong, shares, price):
        self.time = float(time)
        self.isLong = isLong
        self.shares = int(shares)
        self.sharesRemaining = int(shares)
        self.price = float(price)
        self.initialCost = self.shares * self.price
        self.valuePerShare = - self.price / self.shares
        self.trades = [] 
        self.possibleTrades = [];


def insertSort(alist, elm, key=lambda v:v):
    low = 0
    high = len(alist)
    val = key(elm)

    while (low < high):
        middle = (low + high) // 2
        if (key(alist[middle]) < val):
            low = middle + 1
        else:
            high = middle

    alist.insert(low, elm)


def readQuotes(quoteFile):
    quotes = []
    with open(quoteFile, "rb") as f:
        word = f.read(4)
        while word:
            # Add a datapoint for each quote
            # The quote is read in as 5 sequential 4 byte words in little endian
            # Convert the prices to dollars when instantiating
            try: 
                newTime = Quote(struct.unpack('<i', word)[0],
                                    struct.unpack('<i', f.read(4))[0],
                                    struct.unpack('<i', f.read(4))[0],
                                    struct.unpack('<i', f.read(4))[0],
                                    struct.unpack('<i', f.read(4))[0])

                #TODO Will yield a few with -1 as ask
                quotes.append(newTime)

                # Print data for testing
                # print tuple(vars(newTime))
                # print "%d, %d, %d, %d, %d" % tuple(vars(newTime)[a] for a in vars(newTime))
            except:
                #TODO for some reason the last data point isn't being read in
                print "Unable to parse data point for time: %d" % struct.unpack('<i', word)[0]
                print sys.exc_info()

            word = f.read(4)

    # Closes the file auotmatically
    # return the quotes
    return quotes

# Read in the trade data
def readTrades(tradeFile):
    trades = []
    with open(tradeFile, "r") as f:
        line = f.readline()
        while line:
            # Strip the newline character and split on spaces
            tokens = line.rstrip('\n').split()

            # Convert the time to the time to time from midnight
            time_struct = time.gmtime(float(tokens[0]))
            dayms = (time_struct.tm_hour-4) * 60 * 60 + time_struct.tm_min * 60 + time_struct.tm_sec;
            dayms *= 1000

            # Create a new Trade object and add it to the trades array
            newTrade = Trade(dayms, True if tokens[1] == 'B' else False, tokens[2], float(tokens[3]) * 100) 
            trades.append(newTrade)

            line = f.readline()

    # Closes the file automatically 
    # return the trades
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
    
    return lockCrossTime


def calcLockCrossPercentage(quotes):
    # Calculate the total time of the market
    # Convert totalTime to a float to avoid integer division
    totalTime = quotes[-1].time - quotes[0].time
    return (calcLockCrossTime(quotes) / float(totalTime)) * 100

    

# This will display the histogram
def plotSpreadHist(quotes):
    spreads = getSpreadHist(quotes)

    # Set the bins of the histogram and set the data
    maxVal = max(spreads)
    plt.hist(spreads, bins=[i for i in range(1,maxVal)])
    
    # Will limit the x range, but it is hard to see the initial value is 0
    # plt.xlim(1,maxVal)

    # Set the labels of the histogram
    plt.title("Spread Histogram")
    plt.xlabel("Spread (cents)")
    plt.ylabel("Frequency")

    # Display the histogram
    plt.show()


# Plot a histogram of the spread where the frequency is in quote occurrence 
def getSpreadHist(quotes):
    # Create an empty array to store the spreads
    spreads = []

    # For each quote, add the spread value if the spread is greater than 0
    for quote in quotes:
        # Convert to cents and then to integer
        spread = int(quote.askPrice - quote.bidPrice)
        if (spread >= 1): 
            spreads.append(spread)

    return spreads

 


# Calculate all the trades that are valid (Question 4)
def calcValidTrades(allTimes):
    # openOrders is an array of all the orders that haven't been fulfilled
    # validTrades is an array of all the filled trades
    openOrders = []
    validTrades = []
    curQuote = None

    # Iterate over all the information
    for time in allTimes:
        # If the current index is a trade then add it to open orders
        if (isinstance(time, Trade)):
            openOrders.append(Trade(time.time, time.isBuy, time.shares, time.price))

        # If the current index is a valid quote, set the quote to this new quote
        if (isinstance(time, Quote)):
            # Don't do anything in a locked or crossed market
            if (time.askPrice <= time.bidPrice):
                continue
            curQuote = Quote(time.time, time.askShares, time.askPrice, time.bidShares, time.bidPrice)
  
        # Then iterate over all open orders to see if any are able to be filled
        if curQuote is not None:
            # TODO this iteration is slow, if I had it sorted by price then it would be faster
            #       The issue is that I need to serve the orders in order of receiving
            #       A possible way to do this would be to have buckets with a price field
            #       In the bucket would be a timestamp sorted list of trades
            #       Then for each side of the order (bid / ask), 
            #       I could get the first element of each bucket that satisfies the price criteria
            #       Then I could fill the trade of the youngest timestamp 
            #       If there are more shares in whatever bid/ask, 
            #       I could grab the next youngest from the bin I took the youngest in 
            #       and put that into the list for consideration...
            #       Since openOrders never gets that filled, I don't think this is worth it
            for trade in openOrders:
                # If the trade has been filled, remove it from openOrders
                # TODO here I can add in valid trades (not just executed trades)
                if (trade.shares == 0): 
                    openOrders.remove(trade)
                    continue
                
                # TODO Semi repeated logic in this if else
                # If the trade is valid, fill the trade 
                # If the quote had enough shares to fill it, then the trade is removed on next cycle
                # Reduce the available shares from the quote as appropriate
                if (trade.isBuy 
                        and trade.price >= curQuote.askPrice 
                        and curQuote.askShares > 0):
                    # See how many shares I can buy
                    shares = trade.shares if trade.shares <= curQuote.askShares else curQuote.askShares
                    # Append a trade to valid trades
                    validTrades.append(Trade(curQuote.time if curQuote.time > trade.time else trade.time, 
                                                True, shares, curQuote.askPrice))

                    trade.shares -= shares
                    curQuote.askShares -= shares
                
                elif (not trade.isBuy 
                        and trade.price <= curQuote.bidPrice
                        and curQuote.bidShares > 0):
                    # See how many shares I can buy
                    shares = trade.shares if trade.shares <= curQuote.bidShares else curQuote.bidShares
                    # Append a trade to valid trades
                    validTrades.append(Trade(curQuote.time if curQuote.time > trade.time else trade.time,
                                                False, shares, curQuote.bidPrice))
                    
                    trade.shares -= shares
                    curQuote.bidShares -= shares
            
    return validTrades

def printValidTrades(trades):
    for trade in trades:
        print "Time: %i, Price: %.2f, type: %s" % (trade.time, trade.price / 100.0, "buy" if trade.isBuy else "sell") 


# Currently, this employs a greedy algorithm
#   When a valid trade comes into the system, it is compared against each quote for the next minute
#   If the trade (called a position in this code) is first introduced, it will grab any trade entered
#   Once the position has been reduced, then we begin swapping out the trades made with better ones
#   Should a quote with a better value per share be entered.
# TODO
#   I don't think this is optimal
#   One test case I can think of is the following
#       Trades:
#           t=1 b 200s $450
#           t=31 b 200s $450
#       Orders:
#           t=1 ask=200s $450.50   (Trade1 purchased)
#           t=28 bid=200s $450.25
#           t=29 bid=200s $450.20
#           t=31 ask=200s $450.50  (Trade2 purchased)
#           t=40 bid=200s $450.15
#           t=41 bid=200s $450.30
#       Positions
#           t=1 
#               short   200s @ 450.50
#           t=28
#               short   200s @ 450.50
#               buy     200s @ 450.25
#           t=29
#               short   200s @ 450.50
#               buy     200s @ 450.20
#           t=31
#               short   200s @ 450.50
#               buy     200s @ 450.20
#               short   200s @ 450.50
#           t=40
#               short   200s @ 450.50
#               short   200s @ 450.50
#               buy     200s @ 450.15
#           t=41
#               short   200s @ 450.50
#               short   200s @ 450.50
#               buy     200s @ 450.15
#               buy     200s @ 450.30
#       
#       As can be seen, the solution is not optimal
#       This is a slight chance that an order might not be filled, though it is unlikely
#       TODO maybe sort by lowest value per share first?
#           This would not solve all of the issues though... I don't think
#           I implemented a sort
#
# I also considered a graph based solution to this, but could not implement it properly
#   This could have involved some sort of flow with share sized capacities
#       I couldn't incorporate the pricing information properly though
#   Alternatively, some sort of neural net model with backpropogation to increase the value
#       But in this case, I didn't know how to incorporate discrete and fixed capacities
#   A graph model with discrete derivatives would probably be my best bet for an optimal solution
#       This requires post processing of the data, and the storage of most or all possible trades for a position
def optTrader(allTimes):
    # heldPositions are all the positions that are under a minute of opening
    # allPositions are all the positions that were opened
    positions = []
    quote = None

    for i in range(0, len(allTimes)):
        time = allTimes[i]
        # If there is a trade, then see if it is valid
        # If the trade is valid, then add it as a new position into the position arrays
        if (isinstance(time, Trade)):
            trade = time
            if (quote is not None):
                shares = 0
                price = 0;
                if (trade.isBuy 
                        and trade.price >= quote.askPrice 
                        and quote.askShares > 0):
                    # See how many shares I can buy
                    shares = trade.shares if trade.shares <= quote.askShares else quote.askShares
                    quote.askShares -= shares
                    price = quote.askPrice
                
                elif (not trade.isBuy 
                        and trade.price <= quote.bidPrice
                        and quote.bidShares > 0):
                    # See how many shares I can buy
                    shares = trade.shares if trade.shares <= quote.bidShares else quote.bidShares
                    quote.bidShares -= shares
                    price = quote.bidPrice
                
                # Add new positions into the system
                # Add them to the front of heldPositions to get filled (done via insert sort)
                if (shares != 0):
                    position = Position(trade.time, not trade.isBuy, shares, price)
                    heldPositions.insert(0, position)
                    allPositions.append(position)

            
        if (isinstance(time, Quote)):
            # Can't do anything in a locked or crossed market
            if (time.askPrice <= time.bidPrice):
                continue

            # Create a new quote object to avoid altering the original
            quote = Quote(time.time, time.askShares, time.askPrice, time.bidShares, time.bidPrice) 

        # If the next instance is a trade, we want to continue to the next time
        # This will give preference to trades 
        #   It ensures that filling the position will not take preference over initiating one
        if (i < (len(allTimes)-1) and (allTimes[i+1].time == time.time or isinstance(allTimes[i+1], Trade))):
            continue

        # Iterate over the held positions
        for position in heldPositions:
            # If the position has been held for over a minute, then remove it
            if (quote.time > (position.time + 60000)):
                heldPositions.remove(position)
                continue

            # Pass the new quote into the trade
            # This will greedily fill open positions and update the quote object
            position.checkTrade(quote)

            # Uncomment for sorting 
            # Rather slow, but yields slightly better results
            #   Might not be worth the slowdown though
            # heldPositions.remove(position)
            # insertSort(heldPositions, position, key=lambda v: v.valuePerShare)

    return allPositions
    

# It would have been faster to do this inline
# This is better for testing
# I could also return an object with field positions, maxExposure, and profit in last
def calcMaxExposureAndProfit(allPositions):
    # These variables are for questions 5a and 5b
    maxProfit = 0
    maxExposure = 0
    exposure = 0
    openTrades = []

    # Set the correct variables for the first iteration
    #position = allPositions[0]
    #maxProfit += position.calcValue()
    #exposure += position.shares * position.price
    #lastTime = position.time
    #openTrades.extend(position.trades)
    #sorted(openTrades, key=lambda v: v.time)

    # Iterate over the positions taken 
    for position in allPositions:
        # Calculate the max profit for 5a
        maxProfit += position.calcValue()

        # Set the max exposure 
        if (exposure > maxExposure):
            maxExposure = exposure

        # Iterate over the trades taken by the position in order of time
        for trade in openTrades:
            # Break the loop if we have reached the current time
            # All of these trades take place after the addition of the new exposure
            if (trade.time >= position.time):
                break

            # Reduce the exposure by the amount of the position closed
            exposure -= trade.shares * trade.price
            # Remove the trade from openTrades
            openTrades.remove(trade)


        # Add the new exposure to the exposure variable
        # Add in the extra trades taken to close the position
        # Sort the trades in terms of timestamp
        exposure += position.shares * position.price
        for trade in position.trades:
            # Ensure that the trade price is the position price for this algorithm
            openTrades.append(Trade(trade.time, trade.isBuy, trade.shares, position.price))
        sorted(openTrades, key=lambda v: v.time)

    result = {}
    result["maxProfit"] = maxProfit / 100
    result["maxExposure"] = maxExposure / 100
    return result


def printAllPositions(allPositions):
    # Print out the open and closed trades
    for position in allPositions:
        print "Opened: %i, %i, %.2f, %s" % (position.time, position.shares, position.price / 100.0, position.isLong)
        for trade in position.trades:
            print "Closed: %i, %i, %.2f, %s" % (trade.time, trade.shares, trade.price / 100.0, trade.isBuy)

 
# 


def newOpt(positions):
    for position in positions:
        for trade in position.trades:






# TODO Could speed up by generators on the quotes and trades
def main():
    # Read in both quotes and trades
    quotes = readQuotes("aapl.data")
    trades = readTrades("trades.txt")

    # Comine quotes and trades into a list sorted by the time
    # Ensure that quotes are added before trades if the times are equal
    allTimes = sorted(quotes + trades, key=lambda x: (x.time, isinstance(x, Trade)))

    # Question 2
    print "Percent of time locked or crossed: %.3f%%" % calcLockCrossPercentage(quotes)
    
    # Question 3
    # This method is blocking, could alternatively save it and not display
    print "WARNING: This histogram will block. Close the window to continue to questions 4 and 5."
    plotSpreadHist(quotes)
    
    # Question 4
    validTrades = calcValidTrades(allTimes)
    # printValidTrades(validTrades)

    # Question 5
    positions = optTrader(allTimes)
    result = calcMaxExposureAndProfit(positions)
    print "The max profit is $%.2f" % result["maxProfit"]
    print "The number of positions taken was %i" % len(positions)
    print "The profit per position was $%.2f" % (result["maxProfit"] / len(positions))
    print "The max exposure was $%.2f" % result["maxExposure"]
    # printAllPositions(positions)


if __name__ == "__main__":
    main()
