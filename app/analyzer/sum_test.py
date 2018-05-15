from nlp.sum_basic import sum_basic
from nlp.divrank import divrank


def main():
    lines = []
    for fname in ('1.txt',):
        with open('./nlp/data/' + fname, 'r') as file:
            lines += file.readlines()
    print('Sumbasic:', sum_basic(' '.join(lines)))
    print('Divrank:', divrank(' '.join(lines)))

if __name__ == '__main__':
    main()