import mysql.connector
from mysql.connector import Error
from Classes import *

# Establish the connection
def get_connection():
    try:
        connection = mysql.connector.connect(
            host="mysql49-farm1.kinghost.net",
            user="trabalho05_add1",
            password="u4UZHC699W4",  # Consider using environment variables for credentials
            database="trabalhovigiad05"
        )
        if connection.is_connected():
            print("Successfully connected to MySQL database")
        return connection
    except Error as err:
        print(f"MySQL Error: {err}")
        return None

def insert_sliced_image(conn, sliced_image):
    sql = """
        INSERT INTO SlicedImage (uuid, img_name, block, par_num, value)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (sliced_image.uuid, sliced_image.img_name, sliced_image.block, sliced_image.par_num, sliced_image.value)
    with conn.cursor() as cursor:
        cursor.execute(sql, values)
    conn.commit()

def edit_sliced_image(conn, uuid, **kwargs):
    fields = ', '.join([f"{k}=%s" for k in kwargs])
    sql = f"UPDATE SlicedImage SET {fields} WHERE uuid=%s"
    values = list(kwargs.values()) + [uuid]
    with conn.cursor() as cursor:
        cursor.execute(sql, values)
    conn.commit()

def get_sliced_image(conn, uuid):
    sql = "SELECT uuid, img_name, block, par_num, value FROM SlicedImage WHERE uuid=%s"
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(sql, (uuid,))
        row = cursor.fetchone()
        if row:
            return SlicedImage(**row)
    return None

def remove_sliced_image(conn, uuid):
    sql = "DELETE FROM SlicedImage WHERE uuid=%s"
    with conn.cursor() as cursor:
        cursor.execute(sql, (uuid,))
    conn.commit()

def insert_uber_offered_ride(conn, ride):
    sql = """
        INSERT INTO UberOfferedRide (
            img_src, processed_img_src, uuid, ride_value, passenger_score,
            distance_pickup_km, distance_pickup_time, distance_travel_km,
            distance_travel_time, pickup_address, drop_address
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        ride.img_src, ride.processed_img_src, ride.uuid, ride.ride_value, ride.passenger_score,
        ride.distance_pickup_km, ride.distance_pickup_time, ride.distance_travel_km,
        ride.distance_travel_time, ride.pickup_address, ride.drop_address
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, values)
    conn.commit()

def edit_uber_offered_ride(conn, uuid, **kwargs):
    fields = ', '.join([f"{k}=%s" for k in kwargs])
    sql = f"UPDATE UberOfferedRide SET {fields} WHERE uuid=%s"
    values = list(kwargs.values()) + [uuid]
    with conn.cursor() as cursor:
        cursor.execute(sql, values)
    conn.commit()

def get_uber_offered_ride(conn, uuid):
    sql = """
        SELECT img_src, processed_img_src, uuid, ride_value, passenger_score,
               distance_pickup_km, distance_pickup_time, distance_travel_km,
               distance_travel_time, pickup_address, drop_address
        FROM UberOfferedRide WHERE uuid=%s
    """
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(sql, (uuid,))
        row = cursor.fetchone()
        if row:
            return UberOfferedRide(**row)
    return None

def remove_uber_offered_ride(conn, uuid):
    sql = "DELETE FROM UberOfferedRide WHERE uuid=%s"
    with conn.cursor() as cursor:
        cursor.execute(sql, (uuid,))
    conn.commit()


