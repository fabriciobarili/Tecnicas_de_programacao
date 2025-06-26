class UberOfferedRide:
    _rides = []

    def __init__(self, img_src, processed_img_src, uuid, ride_value, passenger_score, distance_pickup_km, 
                 distance_pickup_time, distance_travel_km, distance_travel_time, 
                 pickup_address, drop_address):
        self.img_src = img_src
        self.processed_img_src = processed_img_src
        self.uuid = uuid
        self.ride_value = ride_value
        self.passenger_score = passenger_score
        self.distance_pickup_km = distance_pickup_km
        self.distance_pickup_time = distance_pickup_time
        self.distance_travel_km = distance_travel_km
        self.distance_travel_time = distance_travel_time
        self.pickup_address = pickup_address
        self.drop_address = drop_address

    @classmethod
    def create(cls, *args, **kwargs):
        ride = cls(*args, **kwargs)
        cls._rides.append(ride)
        return ride

    @classmethod
    def get(cls, uuid):
        for ride in cls._rides:
            if ride.uuid == uuid:
                return ride
        return None

    @classmethod
    def remove(cls, uuid):
        ride = cls.get(uuid)
        if ride:
            cls._rides.remove(ride)
            return True
        return False

    def edit(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class SlicedImage:
    _images = []

    def __init__(self, uuid, img_name, block, par_num, value):
        self.uuid = uuid
        self.img_name = img_name
        self.block = block
        self.par_num = par_num
        self.value = value

    @classmethod
    def create(cls, uuid, img_name, block, par_num, value):
        image = cls(uuid, img_name, block, par_num, value)
        cls._images.append(image)
        return image

    @classmethod
    def get(cls, uuid):
        for image in cls._images:
            if image.uuid == uuid:
                return image
        return None

    @classmethod
    def remove(cls, uuid):
        image = cls.get(uuid)
        if image:
            cls._images.remove(image)
            return True
        return False

    def edit(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)