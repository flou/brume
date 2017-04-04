import crayons


class Color():

    @staticmethod
    def for_status(status):
        colors_map = {
            # ERRORS
            # 1 == red
            'CREATE_FAILED': crayons.red,
            'DELETE_FAILED': crayons.red,
            'UPDATE_FAILED': crayons.red,
            'ROLLBACK_IN_PROGRESS': crayons.red,
            'ROLLBACK_FAILED': crayons.red,
            'UPDATE_ROLLBACK_FAILED': crayons.red,

            # COMPLETE
            # 2 == green
            'ROLLBACK_COMPLETE': crayons.green,
            'CREATE_COMPLETE': crayons.green,
            'DELETE_COMPLETE': crayons.green,
            'UPDATE_COMPLETE': crayons.green,
            'UPDATE_ROLLBACK_COMPLETE': crayons.green,

            # SUCCESS
            # 3 == yellow
            'CREATE_IN_PROGRESS': crayons.yellow,
            'DELETE_IN_PROGRESS': crayons.yellow,
            'UPDATE_IN_PROGRESS': crayons.yellow,
            'UPDATE_ROLLBACK_IN_PROGRESS': crayons.yellow,
            'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': crayons.yellow,
            'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': crayons.yellow,

            # SKIPPED
            # 8 == grey
            'DELETE_SKIPPED': crayons.cyan,
        }
        return '{}'.format(colors_map[status](status))


def red(string):
    return '{}'.format(crayons.red(string))


def green(string):
    return '{}'.format(crayons.green(string))
