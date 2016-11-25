from colors import color


class Color():

    @staticmethod
    def for_status(status):
        colors = {
            'red': 1,
            'green': 2,
            'yellow': 3,
            'grey': 8,
        }

        colors_map = {
            # ERRORS
            # 1 == red
            'CREATE_FAILED': colors['red'],
            'DELETE_FAILED': colors['red'],
            'UPDATE_FAILED': colors['red'],
            'ROLLBACK_IN_PROGRESS': colors['red'],
            'ROLLBACK_FAILED': colors['red'],
            'UPDATE_ROLLBACK_FAILED': colors['red'],

            # COMPLETE
            # 2 == green
            'ROLLBACK_COMPLETE': colors['green'],
            'CREATE_COMPLETE': colors['green'],
            'DELETE_COMPLETE': colors['green'],
            'UPDATE_COMPLETE': colors['green'],
            'UPDATE_ROLLBACK_COMPLETE': colors['green'],

            # SUCCESS
            # 3 == yellow
            'CREATE_IN_PROGRESS': colors['yellow'],
            'DELETE_IN_PROGRESS': colors['yellow'],
            'UPDATE_IN_PROGRESS': colors['yellow'],
            'UPDATE_ROLLBACK_IN_PROGRESS': colors['yellow'],
            'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': colors['yellow'],
            'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': colors['yellow'],

            # SKIPPED
            # 8 == grey
            'DELETE_SKIPPED': colors['grey'],
        }
        return color(status, fg=colors_map[status])


if __name__ == '__main__':
    for i in range(15):
        print color('Color #%d' % i, fg=i)
