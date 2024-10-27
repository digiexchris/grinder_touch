import os
import semiauto_sg

VCP_DIR = os.path.realpath(os.path.dirname(__file__))
VCP_CONFIG_FILE = os.path.join(VCP_DIR, 'config.yml')


def main(opts=None):
    semiauto_sg.main('sg', opts)


if __name__ == '__main__':
    main()
