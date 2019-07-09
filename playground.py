def do_stuff():
    print("doing stuff")
    raise RuntimeError("Something went wrong")

def main():
    try:
        do_stuff()
    except:
        print("do stuff raised an exception")
    else:
        print("do stuff went smoothly")


main()