long = 69.275769
lat = 41.342221
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="Backend")
# location = geolocator.reverse(f"{lat}, {long}")
# print(location)
# address = location.raw['address']
# print(address['county'], address['road'], address['neighbourhood'])
