# TODO consider a child object of trade for the max logic
# TODO I don't know if this will give the best
#       Consider the case where we actually wanted to sell the old shares earlier or later
#       Due to the other positions we own
#       Also, what if we want to use this trade in another trade situation?
#       I may want to throw all the open positions in the same trade object
# TODO If a trade is forced out of the currentTrades, it might be good for an older trade
#       Consider the case where there are two trades 30 seconds apart
#       If good trades come in at 29 seconds, and the best come in at 31 seconds
#       Then the first trade will take all the best
#       So this is 31 seconds where the trades are best
#       The second trade doesn't have access to the 29 seconds, so that is not good
# MAX FLOW MIN CUT
# This is a greedy algorithm which takes the best sale at a given time
class OptimalTrade:
    def checkNewTrade(self, trade):
        valuePerShare = trade.price - self.price
        sharesToPurchase = 0

        # If we still own shares of this trade, then sell them
        if (self.sharesRemaining != 0):
            sharesToPurchase = trade.shares if trade.shares >= self.sharesRemaining else self.sharesRemaining

        # Update the trade with the number of shares left to use
        trade.shares -= sharesToPurchase

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


    def __init__(self, time, isBuy, shares, price):
        self.time = float(time)
        self.isBuy = True if isBuy == 'B' else False
        self.shares = int(shares)
        self.price = float(price)
        self.currentTrades = []
        self.curValue = sys.float_info.min
        self.sharesRemaining = int(shares)


The best way to solve the number 5 that I have thought of is max flow min cut. 
This graph would have the source and sink, and two layers. The first layer would be 
the nodes I could buy. These have the purchase price (price * share) flowing from 
source to the node. The second layer would be all the purchaseable trades
(people we can sell to). There would be links from all first nodes
to the second where the second node is within a minute of the first.
The capacity of second layer to sink would be the price of the node
times the number of shares.
def plotHistSpreadVsTime(quotes):
    spreads = []
    lastTime = 0

    for quote in quotes:
        if (lastTime == 0):
            lastTime = quote.time
            spread = quote.askPrice - quote.bidPrice
            continue

        timeDelta = quote.time - lastTime
        spreads += timeDelta * [spread]
        spread = quote.askPrice - quote.bidPrice

    plt.hist(spreads, bins=[i for i in xrange(0,max(spreads))])
    plt.title("Spread Histogram")
    plt.xlabel("Spread")
    plt.ylabel("Time")
    plt.show()

OLD VERSION OF CALC TRADES... NEVER USED
# Can use the quote changes in volume right?
def calcValidTrades(quotes, trades):
    quoteIndex = 0
    activeTrades = [];
    completedTrades = [];

    for trade in trades: 
        quote = quotes[quoteIndex]
        while (quote.time < trade.time):
            quoteIndex += 1
            quote = quote[quoteIndex]

        activeTrades.append(trade)
        for atrade in activeTrades:
            if (atrade.isBuy and quote.askPrice <= atrade.askPrice):
                if (atrade.shares < quote.askShare):
                    activeTrades.remove(trade)
                    quote.askShare -= atrade.shares
                    newTrade = trade(quote.time, True, trade.shares, quote.askPrice)
                    completedTrades.append(newTrade)
                else:
                    numTraded = quote.askShare
                    trade.shares -= quote.askShare
                    quote.askShare = 0
                    newTrade = trade(quote.time, True, numTraded, quote.askPrice)
                    completedTrades.append(newTrade)
            if (not atrade.isBuy and quote.bidPrice >= atrade.bidPrice):
                if (atrade.shares < quote.bidShare):
                    activeTrades.remove(trade)
                    quote.bidShare -= atrade.shares
                    newTrade = trade(quote.time, True, trade.shares, quote.bidPrice)
                    completedTrades.append(newTrade)
                else:
                    numTraded = quote.bidShare
                    trade.shares -= quote.bidShare
                    quote.bidShare = 0
                    newTrade = trade(quote.time, True, numTraded, quote.bidPrice)
                    completedTrades.append(newTrade)




THIS ONE WILL CALCULATE TRADES BUT SORTS THEM BY PRICE
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
            


# TODO  might be cool to have a gradient descent like algorithm
#       Look into this
def crossingTrades(quotes, trades):
    tradeIndex = 0
    isCrossed = False
    heldPositions = []
    transactions = []

    # Iterate over the quotes
    for (quote in quotes): 
        if (len(heldPositions) != 0):
            held = heldPositions[0];

        trade = trade[tradeIndex]

        # If a given trade is active an has not been purchased while the market is crossed
        # then we must fill that order
        if (trade.time > quote.time and isCrossed):
            heldPositions.append(Trade(trade.time, True, trade.shares, trade.price))
            # Also add the trade into transactions to keep a record of all transactions
            transactions.append(Trade(trade.time, True, trade.shares, trade.price))

        # If the ask price is less than the bid price we have a crossed market
        # Set the flag appropriately
        if (quote.askPrice < quote.bidPrice):
            isCrossed = True
        else:
            isCrossed = False

        # Iterate over the trades until we find one where the 
        while (trade.time < quote.time):
            trade = trade[tradeIndex]
            tradeIndex += 1


THIS IS IF WE ASSUME ONLY FILLED UP TO THE QUOTE SIZE
    Probably not currect because I think we only want sale orders
# TODO  might be cool to have a gradient descent like algorithm
#       Look into this
# TODO this will probably mutate the underlying quotes object
def crossingTrades(quotes, trades):
    tradeIndex = 0
    isCrossed = False
    heldPositions = []
    unfilledBids = []

    # Iterate over the quotes
    for (quote in quotes): 
        trade = trade[tradeIndex]

        # If we have unfilled bids and the market is crossed
        # Make sure these are delt with first
        while (len(unfilledBids) != 0 and isCrossed and quote.askShares != 0):


        # If a given trade is active an has not been purchased while the market is crossed
        # then we must fill that order
        if (trade.time > quote.time and isCrossed):
            # If we can fill the whole order, then do so
            if (trade.shares < quote.askShares):
                heldPositions.append(Trade(trade.time, True, trade.shares, trade.price))
                tradeIndex += 1
            else:
                heldPositions.append(Trade(trade.time, True, quote.askShares, trade.price))
                unfilledBids.append(Trade(trade.time, True, trade.shares - quote.askShares, trade.price))

        # If the ask price is less than the bid price we have a crossed market
        # Set the flag appropriately
        if (quote.askPrice < quote.bidPrice):
            isCrossed = True
        else:
            isCrossed = False

        # Iterate over the trades until we find one where the 
        while (trade.time < quote.time):
            trade = trade[tradeIndex]
            tradeIndex += 1

