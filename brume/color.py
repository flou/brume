from colors import color


class Color():

    @staticmethod
    def for_status(status):
        colors_map = {
            # ERRORS
            # 1 == red
            'CREATE_FAILED': 1,
            'DELETE_FAILED': 1,
            'UPDATE_FAILED': 1,
            'ROLLBACK_IN_PROGRESS': 1,
            'ROLLBACK_FAILED': 1,
            'UPDATE_ROLLBACK_FAILED': 1,

            # COMPLETE
            # 2 == green
            'ROLLBACK_COMPLETE': 2,
            'CREATE_COMPLETE': 2,
            'DELETE_COMPLETE': 2,
            'UPDATE_COMPLETE': 2,
            'UPDATE_ROLLBACK_COMPLETE': 2,

            # SUCCESS
            # 3 == yellow
            'CREATE_IN_PROGRESS': 3,
            'DELETE_IN_PROGRESS': 3,
            'UPDATE_IN_PROGRESS': 3,
            'UPDATE_ROLLBACK_IN_PROGRESS': 3,
            'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': 3,
            'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': 3,

            # SKIPPED
            # 8 == grey
            'DELETE_SKIPPED': 8,
        }
        return color(status, fg=colors_map[status])


if __name__ == '__main__':
    for i in range(15):
        print color('Color #%d' % i, fg=i)
