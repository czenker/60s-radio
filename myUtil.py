kHz = 1000
MHz = 1_000_000

minCap = 557
maxCap = 867

def capToUkw(cap):
  # totally scientific interpolation by wolfram alpha
  # @see https://www.wolframalpha.com/input/?i=polynomial+fit+%7B%7B854%2C88%7D%2C+%7B842%2C90%7D%2C+%7B824%2C92%7D%2C+%7B799%2C94%7D%2C+%7B762%2C96%7D%2C+%7B715%2C98%7D%2C+%7B670%2C100%7D%2C+%7B622%2C102%7D%2C+%7B568%2C104%7D%7D
  return ((((-7.00277e-9 * cap + 1.91371e-5) * cap - 1.95386e-2) * cap + 8.78978) * cap - 1362.96) * MHz

def capToKw(cap):
  return ((-1.9404e-6 * cap - 2.46053e-3) * cap + 9.41234) * MHz

def capToMw(cap):
  return ((-1.28739e-3 * cap - 1.6275 ) * cap + 2865.01) * kHz

def capToLw(cap):
  return ((((-2.10644e-6 * cap + 3.53102e-3) * cap - 2.44247) * cap) + 974.141) * kHz

minLw = capToLw(maxCap)
maxLw = capToLw(minCap)
minMw = capToMw(maxCap)
maxMw = capToMw(minCap)
minKw = 5.9 * MHz
maxKw = 7.35 * MHz
minUkw = capToUkw(maxCap)
maxUkw = capToUkw(minCap)


serialPort = "/dev/ttyUSB0"
serialBaud = 500000

ledPin = 12
