from summarizers.sum_basic import sum_basic
from summarizers.divrank import divrank


def main():
    lines = []
    for fname in ('1.txt','2.txt'):
        with open('./summarizers/data/' + fname, 'r') as file:
            lines += file.readlines()
    print('Sumbasic:', sum_basic(' '.join(lines)))
    print('Divrank:', divrank(' '.join(lines)))

if __name__ == '__main__':
    main()