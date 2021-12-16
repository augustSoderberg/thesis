def pnt():
    message, items = get()
    print(message.format(items))

def get():
    return ("hello {}".format("{}"), [1, 2, 3])

if __name__ == '__main__':
    prompt = ""
    for i in range(5):
        prompt += "HI"
    print(prompt)