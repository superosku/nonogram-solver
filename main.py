class UnsolvableStateException(Exception):
    pass


class SolvedException(Exception):
    pass


class Solver:
    def __init__(
        self,
        row_input=None,
        column_input=None,
        input_json=None,
        rows=None,
        columns=None
    ):
        if input_json:
            self.columns = input_json['columns']
            self.rows = input_json['rows']
        if row_input:
            self.columns = [
                [int(i) for i in l.split(',')] for l in column_input.split('/')
            ]
            self.rows = [
                [int(i) for i in l.split(',')] for l in row_input.split('/')
            ]
        if rows:
            self.rows = rows
            self.columns = columns

        self.rows_dirty = [True for _ in range(len(self.rows))]
        self.columns_dirty = [True for _ in range(len(self.columns))]

        self.table = [
            [
                0
                for _ in range(len(self.columns))
            ]
            for _ in range(len(self.rows))
        ]

        self.hardness_index = 2
        self.changes_table = True

    def clone(self):
        new_solver = Solver(
            rows=self.rows,
            columns=self.columns
        )
        new_solver.table = [i[:] for i in self.table]  # Deep copy

        return new_solver


    def is_solved(self):
        all_filled = not any([
            any([
                c == 0
                for c in row
            ])
            for row in self.table
        ])

        return all_filled

    def print_table(self):
        print('Table:')

        for i in range(13):
            print(' ' * 15, end='')
            for column_index, column in enumerate(self.columns):
                column = (
                        ('D' if self.columns_dirty[column_index] else ' ') +
                        ' '.join([str(s) for s in column]) + ' ' * 100
                )
                # column = column + [' '] * 5
                print(str(column[i]), end='')
            print('')

        for row_index, row_text in enumerate([
            ''.join([{0: '-', 1: ' ', 2: '#'}[i] for i in t])
            for t in self.table
        ]):
            print(
                ('D' if self.rows_dirty[row_index] else ' ') +
                ','.join([str(i) for i in self.rows[row_index]]).ljust(15) +
                row_text
            )

    def possibilities(self, choices, length, usability_mask, gather_all_choices=False):
        true_mask = [[False, False] for _ in range(length)]
        all_choices = []

        def rec_possibilities(remaining_choices, free_index, mask):
            if not remaining_choices:
                if not all([
                    (
                        usability_mask == 0 or
                        (usability_mask - 1 == suggested_value)
                    )
                    for suggested_value, usability_mask in
                    zip(mask, usability_mask)
                ]):
                    return

                if gather_all_choices:
                    all_choices.append(mask[:])
                for i, value in enumerate(mask):
                    true_mask[i][value] = True
                return
            for i in range(free_index, length - remaining_choices[0] + 1):
                # If a block can't be placed here anymore, skip the recursion
                if any([
                    p == 1 for p in usability_mask[i:i + remaining_choices[0]]
                ]):
                    continue
                # If such a space can't be left between this and previous
                # block, skip the recursion
                if any([
                    p == 2 for p in usability_mask[free_index:i]
                ]):
                    continue

                for j in range(remaining_choices[0]):
                    mask[i + j] = 1
                rec_possibilities(remaining_choices[1:],
                                  i + remaining_choices[0] + 1, mask)
                for j in range(remaining_choices[0]):
                    mask[i + j] = 0

        rec_possibilities(choices, 0, [0] * length)

        if any(
            a is False and b is False
            for a, b in true_mask
        ):
            raise UnsolvableStateException('Unsolvable state')

        if gather_all_choices:
            return all_choices

        return true_mask

    def do_pass(self):
        for y, column in enumerate(self.columns):
            if len(column) > self.hardness_index:
                continue
            if not self.columns_dirty[y]:
                continue

            usability_mask = [self.table[x][y] for x in range(len(self.rows))]
            mask = self.possibilities(column, len(self.rows), usability_mask)
            for x, (possible_empty, possible_full) in enumerate(mask):
                if (
                        possible_empty and
                        not possible_full and
                        self.table[x][y] == 0
                ):
                    self.rows_dirty[x] = True
                    self.table[x][y] = 1
                    self.changes_table = True
                if (
                        not possible_empty and
                        possible_full and self.table[x][y] == 0
                ):
                    self.rows_dirty[x] = True
                    self.table[x][y] = 2
                    self.changes_table = True

            self.columns_dirty[y] = False

        for x, row in enumerate(self.rows):
            if len(row) > self.hardness_index:
                continue
            if not self.rows_dirty[x]:
                continue

            usability_mask = [self.table[x][y] for y in
                              range(len(self.columns))]
            mask = self.possibilities(row, len(self.columns), usability_mask)
            for y, (possible_empty, possible_full) in enumerate(mask):
                if (
                        possible_empty and
                        not possible_full and
                        self.table[x][y] == 0
                ):
                    self.columns_dirty[y] = True
                    self.table[x][y] = 1
                    self.changes_table = True
                if (
                        not possible_empty and
                        possible_full and
                        self.table[x][y] == 0
                ):
                    self.columns_dirty[y] = True
                    self.table[x][y] = 2
                    self.changes_table = True

            self.rows_dirty[x] = False

        if not self.changes_table and self.hardness_index < 20:
            self.changes_table = True
            self.hardness_index += 1

    def guess_slowly(self):
        for i in range(len(self.rows_dirty)):
            self.rows_dirty[i] = True
        for i in range(len(self.columns_dirty)):
            self.columns_dirty[i] = True

        best = None

        for x in range(len(self.rows)):
            usability_mask = [self.table[x][y] for y in
                              range(len(self.columns))]
            choice_options = self.possibilities(
                self.rows[x], len(self.columns), usability_mask, True
            )
            if (
                    len(choice_options) > 1 and
                    (best is None or len(choice_options) < len(best[2]))
            ):
                best = (
                    x,
                    None,
                    choice_options
                )

        for y in range(len(self.columns)):
            usability_mask = [self.table[x][y] for x in
                              range(len(self.rows))]
            choice_options = self.possibilities(
                self.columns[y], len(self.rows), usability_mask, True
            )
            if (
                    len(choice_options) > 1 and
                    (best is None or len(choice_options) < len(best[2]))
            ):
                best = (
                    None,
                    y,
                    choice_options
                )

        x, y, choice_options = best

        for choice_option in choice_options:
            if x is None:
                new = self.clone()
                for x in range(len(self.rows)):
                    new.table[x][y] = choice_option[x] + 1
                try:
                    new.solve_internal()
                except UnsolvableStateException:
                    pass

                if new.is_solved():
                    raise SolvedException('Solved')
                x = None

            if y is None:
                new = self.clone()
                for y in range(len(self.columns)):
                    new.table[x][y] = choice_option[y] + 1
                try:
                    new.solve_internal()
                except UnsolvableStateException:
                    pass

                if new.is_solved():
                    raise SolvedException('Solved')
                y = None

    def solve_internal(self):
        self.print_table()
        for i in range(100):
            self.changes_table = False
            self.do_pass()
            if not self.changes_table:
                if not self.is_solved():
                    self.guess_slowly()
                else:
                    self.print_table()
                    raise SolvedException('Solved')
                break
            self.print_table()

    def solve(self):
        try:
            self.solve_internal()
        except SolvedException:
            print('')
            print(' ' + '*' * 30)
            print(' * SOLVED :))))))))')
            print(' ' +  '*' * 30)


# solver = Solver("2/1,2/1,2/3/4", "1/5/2/4/2,1")
# solver.solve()
#
# solver = Solver("3/2,1/3,2/2,2/6/1,5/6/1/2", "1,2/3,1/1,5/7,1/5/3/4/3")
# solver.solve()
#
# solver = Solver("2/2/2/4/2/2", "0/1/6/6/1/0/0")
# solver.solve()

# solver = Solver(
#     "8,7,5,7/5,4,3,3/3,3,2,3/4,3,2,2/3,3,2,2/3,4,2,2/4,5,2/3,5,1/4,3,2/3,4,2/4,4,2/3,6,2/3,2,3,1/4,3,4,2/3,2,3,2/6,5/4,5/3,3/3,3/1,1",
#     "1/1/2/4/7/9/2,8/1,8/8/1,9/2,7/3,4/6,4/8,5/1,11/1,7/8/1,4,8/6,8/4,7/2,4/1,4/5/1,4/1,5/7/5/3/1/1"
# )
# solver.solve()

# solver = Solver(
#     "1,1/1,1/3/4/4/2,6/2,2,2/4,2,2/3,1,2,1/1,2,2,1,1/1,1,2,1/2,4,1/2,1,2/7,4",
#     "1,2/4/10/8,2/1,3,2/2,2,1/2,1,1/1,2,1,1/1,1,1,1,1/1,2,2,1/1,3,1/2,1/2,1,1/4,2/2/1"
# )
# solver.solve()
#
# solver = Solver(
#     "8/13/17/4,14/3,3,3/3,2,10,2/2,2,11,2/2,2,12,1/2,2,12,1/3,1,4,4,1/3,2,4,4,1/2,2,12,1/3,2,11,1/6,9,1/11,7/10,5/16/7,5/4,5/4,5",
#     "3/8/4,5/3,3/3,5,3/2,3,6/3,2,5/2,2,4/4,3/5,4/4,15/4,15/4,15/4,15/4,4,3,2/4,4,4,2/4,4,6/3,4,7/3,15/2,8,6/3,7,6/2,5,1,4/2,1,2/2,1/6"
# )
# solver.solve()
#
# solver = Solver(
#     "4/6/2,3/2/3,1,3/1,5,1/1,1/1,2,1/1,1,1/1,1/1,1/1,1/1,1/2,1,2/3,3",
#     "5/1,2/1,1,1/1,2,2/1,2,1/2,1,1/1,3,1/2,1,1/3,2,1/3,1,2/3,1,1/1,1,2/5"
# )
# solver.solve()
#
# solver = Solver(
#     "1,3/2,2/2,3/2,1,2/1,3/2,3/2,4/3,4/4,5/5,5/3,6/2,1,1/12/8/15",
#     "1,1/2,1,1/2,1,2,1/2,2,1,1/4,3/6,3/12/2,3/15/1,9,3/1,7,3/5,3/3,1,1/1,1,1/1"
# )
# solver.solve()

# solver = Solver(
#     input_json={
#         "columns": [
#             [1],
#             [0],
#             [1],
#             [0],
#             [1],
#             [0],
#             [1],
#             [0],
#             [1],
#             [0],
#             [1]
#         ],
#         "rows": [
#             [1, 1, 1],
#             [0],
#             [1, 1, 1]
#         ]
#     }
# )
# solver.solve()

# solver = Solver(
#     input_json={
#         "columns": [
#             [4],
#             [9],
#             [11],
#             [13],
#             [4, 5],
#             [3, 4],
#             [3, 4, 3],
#             [3, 4, 6],
#             [8, 4, 8],
#             [6, 5, 10],
#             [2, 5, 4, 3],
#             [9, 5, 3, 3],
#             [11, 5, 3, 4],
#             [12, 5, 4, 4],
#             [18, 2, 5, 3],
#             [4, 16, 12, 1],
#             [3, 17, 12],
#             [4, 18, 3, 5],
#             [3, 19, 4, 2],
#             [6, 10, 9, 1],
#             [7, 10, 7, 2],
#             [2, 9, 4, 2],
#             [14, 2],
#             [3, 17, 3],
#             [4, 25, 3],
#             [8, 27, 5],
#             [45],
#             [27, 12],
#             [25, 6],
#             [26],
#             [26],
#             [27],
#             [34],
#             [36],
#             [8, 27],
#             [6, 27],
#             [2, 12, 9],
#             [12, 6],
#             [14, 5],
#             [15, 5],
#             [15, 4],
#             [3, 4, 11, 4],
#             [7, 4, 10, 4, 3],
#             [3, 10, 5, 5, 3, 4],
#             [2, 8, 5, 4, 3, 5],
#             [1, 6, 4, 4, 1, 3, 2],
#             [5, 6, 3, 2],
#             [5, 7, 4, 3],
#             [13, 8, 8],
#             [13, 5, 3, 5],
#             [13, 3, 3],
#             [13, 2, 3],
#             [3, 2, 3],
#             [3, 3, 3],
#             [3, 4, 5],
#             [3, 2, 9],
#             [4, 2, 6],
#             [8, 2],
#             [4]
#         ],
#         "rows": [
#             [1],
#             [1, 2],
#             [2, 7],
#             [3, 10],
#             [3, 11, 4],
#             [2, 12, 3],
#             [4, 13, 3],
#             [5, 13, 2],
#             [5, 12, 3],
#             [6, 11, 3, 4],
#             [5, 10, 4, 6],
#             [4, 8, 3, 8],
#             [4, 11, 3, 4, 3],
#             [4, 12, 3, 4, 2],
#             [4, 13, 4, 4, 3],
#             [5, 4, 13, 5, 4, 2],
#             [7, 5, 13, 7, 4, 2],
#             [8, 7, 20, 4, 2],
#             [4, 34, 4, 3],
#             [3, 3, 29, 4, 3],
#             [3, 2, 28, 5],
#             [4, 2, 28, 6],
#             [4, 1, 38],
#             [4, 39],
#             [5, 40],
#             [46, 7],
#             [13, 30, 7],
#             [11, 6, 6, 12, 3, 4],
#             [8, 5, 6, 13, 2, 3],
#             [5, 5, 4, 7, 3, 3],
#             [4, 5, 4, 7, 2, 4],
#             [4, 5, 4, 8, 3],
#             [4, 4, 5, 14],
#             [2, 4, 4, 5, 11],
#             [7, 4, 4, 5, 9],
#             [8, 4, 4, 6, 2],
#             [5, 4, 4, 4, 7, 2],
#             [4, 3, 3, 3, 10],
#             [4, 3, 4, 3, 14],
#             [4, 6, 3, 14],
#             [4, 6, 3, 14],
#             [12, 3, 3],
#             [9, 3, 3, 2],
#             [9, 3, 3, 2],
#             [2, 3, 4, 3, 3],
#             [3, 3, 6],
#             [2, 4, 5],
#             [3, 4],
#             [1, 8],
#             [4]
#         ]
#     }
# )
# solver.solve()

# solver = Solver(
#     input_json={
#         "columns": [
#             [7, 1, 1, 5, 7],
#             [1, 1, 3, 1, 1, 1],
#             [1, 3, 1, 6, 2, 1, 3, 1],
#             [1, 3, 1, 1, 2, 1, 1, 3, 1],
#             [1, 3, 1, 1, 2, 1, 1, 3, 1],
#             [1, 1, 1, 1, 1, 1, 1],
#             [7, 1, 1, 1, 1, 1, 7],
#             [2, 1, 2],
#             [1, 1, 2, 3, 1, 2, 5],
#             [3, 2, 2, 2, 3, 3],
#             [2, 1, 2, 2, 1, 2, 1, 2],
#             [1, 2, 3, 3],
#             [1, 2, 2, 1, 2, 1, 1, 2, 1, 1],
#             [1, 3, 2, 1, 1, 1, 1, 1],
#             [1, 2, 4, 1, 3, 1, 4],
#             [2, 1, 1, 3, 1, 1, 1, 1],
#             [3, 3, 2, 1, 6, 1],
#             [1, 3, 1, 1, 2, 2],
#             [7, 1, 1, 1, 2],
#             [1, 1, 2, 1, 4, 1],
#             [1, 3, 1, 3, 8, 1],
#             [1, 3, 1, 1, 1, 2, 1],
#             [1, 3, 1, 2, 2, 1, 1, 1],
#             [1, 1, 1, 1, 1, 6, 1],
#             [7, 2, 5, 5]
#         ],
#         "rows": [
#             [7, 1, 1, 1, 1, 7],
#             [1, 1, 1, 1, 1, 2, 1, 1],
#             [1, 3, 1, 1, 3, 1, 3, 1],
#             [1, 3, 1, 3, 3, 1, 3, 1],
#             [1, 3, 1, 1, 1, 1, 3, 1],
#             [1, 1, 2, 6, 1, 1],
#             [7, 1, 1, 1, 1, 1, 7],
#             [3, 3],
#             [5, 4, 1, 2, 1, 1, 1, 1],
#             [2, 1, 2, 1, 2, 1, 1, 1],
#             [4, 1, 1, 1, 4, 1, 3],
#             [4, 1, 1, 1, 2, 1],
#             [3, 1, 2, 2, 4, 2, 3],
#             [1, 1, 1, 1, 1, 1, 1, 1],
#             [1, 1, 1, 1, 5, 1, 2, 2],
#             [1, 1, 1, 1, 1, 2, 1],
#             [1, 1, 1, 2, 3, 12],
#             [1, 1, 1, 1, 2, 2],
#             [7, 2, 1, 1, 1, 1, 2],
#             [1, 1, 2, 1, 1, 1, 1, 1],
#             [1, 3, 1, 2, 9, 3],
#             [1, 3, 1, 1, 1, 3, 2, 2],
#             [1, 3, 1, 2, 3, 1, 1],
#             [1, 1, 4, 3, 1, 1],
#             [7, 5, 1, 2]
#         ]
#     }
# )
# solver.solve()

solver = Solver(
    input_json={
        "columns": [
            [43, 43],
            [38, 38],
            [34, 14, 34],
            [31, 14, 31],
            [29, 11, 29],
            [27, 12, 27],
            [25, 13, 25],
            [24, 14, 24],
            [22, 14, 22],
            [21, 3, 3, 2, 21],
            [19, 19],
            [18, 18],
            [17, 17],
            [16, 16],
            [15, 2, 15],
            [14, 3, 14],
            [13, 4, 13],
            [12, 3, 12],
            [11, 2, 2, 11],
            [10, 5, 2, 10],
            [10, 4, 6, 10],
            [9, 5, 12, 9],
            [8, 4, 16, 8],
            [8, 3, 18, 8],
            [7, 3, 20, 7],
            [6, 2, 20, 6],
            [6, 1, 21, 6],
            [5, 2, 23, 5],
            [5, 2, 2, 24, 5],
            [4, 2, 3, 1, 24, 4],
            [4, 3, 2, 4, 25, 4],
            [3, 3, 3, 5, 25, 4],
            [3, 3, 2, 5, 25, 3],
            [3, 2, 3, 5, 25, 3],
            [2, 3, 3, 2, 4, 25, 2],
            [2, 2, 4, 2, 1, 2, 4, 27, 2],
            [2, 2, 4, 1, 2, 6, 27, 2],
            [2, 2, 5, 1, 5, 5, 27, 2],
            [1, 8, 1, 7, 33, 1],
            [1, 7, 6, 34, 1],
            [1, 6, 7, 2, 36, 2, 1],
            [1, 6, 7, 36, 5, 1],
            [1, 6, 2, 8, 1, 44, 1],
            [3, 2, 9, 2, 2, 46],
            [2, 4, 8, 2, 1, 46],
            [2, 6, 8, 2, 47],
            [6, 9, 49],
            [3, 1, 12, 50],
            [1, 4, 13, 50],
            [2, 3, 2, 15, 50],
            [19, 50],
            [21, 49],
            [19, 3, 48],
            [16, 4, 48],
            [1, 12, 4, 47],
            [15, 5, 46],
            [1, 16, 5, 45],
            [1, 1, 3, 14, 3, 4, 21, 16, 1],
            [1, 1, 16, 11, 29, 4, 2, 1],
            [1, 18, 12, 32, 1],
            [1, 1, 1, 33, 30, 1],
            [1, 41, 28, 1],
            [2, 42, 16, 8, 2],
            [2, 23, 21, 14, 2],
            [2, 22, 21, 12, 1, 2],
            [2, 21, 1, 34, 1, 3, 2],
            [3, 23, 20, 8, 6, 3],
            [3, 24, 6, 13, 7, 6, 3],
            [3, 25, 6, 11, 6, 5, 4],
            [4, 34, 10, 6, 4, 4],
            [4, 34, 8, 4, 2, 4],
            [5, 34, 8, 1, 5],
            [5, 33, 7, 5],
            [6, 33, 7, 6],
            [6, 32, 5, 6],
            [7, 32, 2, 7],
            [8, 31, 8],
            [8, 30, 8],
            [9, 30, 9],
            [10, 29, 10],
            [10, 28, 10],
            [11, 28, 11],
            [12, 28, 12],
            [13, 27, 13],
            [14, 28, 14],
            [15, 30, 15],
            [16, 31, 16],
            [17, 31, 17],
            [18, 30, 18],
            [19, 20, 2, 19],
            [21, 15, 1, 21],
            [22, 13, 22],
            [24, 12, 24],
            [25, 12, 1, 25],
            [27, 10, 27],
            [29, 10, 2, 29],
            [31, 6, 9, 32],
            [34, 5, 34],
            [38, 38],
            [43, 43]
        ],
        "rows": [
            [43, 43],
            [38, 38],
            [34, 1, 34],
            [31, 6, 31],
            [29, 10, 2, 29],
            [27, 6, 8, 2, 1, 5, 27],
            [25, 5, 9, 10, 25],
            [24, 4, 8, 1, 11, 24],
            [22, 4, 9, 2, 1, 13, 22],
            [21, 5, 9, 2, 16, 21],
            [19, 4, 10, 1, 16, 19],
            [18, 4, 4, 20, 18],
            [17, 4, 2, 1, 6, 1, 22, 17],
            [16, 4, 3, 34, 16],
            [15, 5, 8, 27, 15],
            [14, 6, 5, 33, 14],
            [13, 3, 1, 4, 35, 13],
            [12, 3, 2, 6, 36, 12],
            [11, 3, 1, 2, 1, 3, 36, 11],
            [10, 1, 1, 2, 38, 10],
            [10, 2, 1, 1, 1, 38, 10],
            [9, 1, 2, 2, 42, 9],
            [8, 3, 49, 8],
            [8, 52, 8],
            [7, 56, 7],
            [6, 56, 6],
            [6, 28, 26, 6],
            [5, 19, 2, 5, 27, 5],
            [5, 12, 9, 5, 26, 5],
            [4, 7, 2, 8, 5, 25, 4],
            [4, 6, 1, 2, 6, 2, 6, 26, 4],
            [3, 6, 1, 2, 3, 1, 13, 25, 3],
            [3, 4, 1, 3, 15, 25, 3],
            [3, 3, 2, 43, 3],
            [2, 11, 1, 5, 37, 2],
            [2, 13, 37, 2],
            [2, 14, 37, 2],
            [2, 16, 37, 2],
            [1, 18, 4, 39, 1],
            [1, 43, 21, 5, 1],
            [1, 45, 20, 4, 1],
            [1, 47, 9, 4, 1],
            [1, 35, 11, 2, 8, 3, 1],
            [1, 37, 16, 5, 2],
            [1, 38, 15, 5, 2],
            [1, 38, 14, 4, 1, 1],
            [1, 39, 13, 4, 1],
            [1, 40, 13, 4, 2],
            [1, 41, 11, 3, 1],
            [2, 43, 8, 3, 1],
            [2, 43, 7, 2, 2],
            [2, 42, 5, 3, 2],
            [2, 44, 3, 2, 1],
            [2, 45, 2],
            [2, 45, 3, 2],
            [3, 49, 2],
            [3, 49, 1],
            [1, 3, 48, 1, 1],
            [1, 4, 46, 1],
            [1, 5, 35, 1],
            [1, 5, 34, 1],
            [1, 6, 30, 1],
            [2, 7, 29, 2],
            [2, 6, 28, 2],
            [2, 6, 19, 7, 2],
            [2, 5, 19, 6, 2],
            [3, 4, 19, 5, 3],
            [3, 4, 24, 3],
            [3, 4, 22, 4],
            [4, 3, 23, 4],
            [4, 4, 22, 4],
            [5, 3, 22, 5],
            [5, 3, 22, 5],
            [6, 1, 16, 4, 2, 6],
            [6, 2, 17, 4, 3, 6],
            [7, 1, 22, 3, 7],
            [8, 23, 4, 8],
            [8, 21, 4, 8],
            [9, 18, 3, 9],
            [10, 16, 3, 10],
            [10, 17, 4, 10],
            [11, 16, 2, 11],
            [12, 15, 12],
            [13, 14, 13],
            [14, 12, 14],
            [15, 10, 15],
            [16, 8, 16],
            [17, 6, 17],
            [18, 18],
            [19, 19],
            [21, 21],
            [22, 22],
            [24, 24],
            [25, 25],
            [27, 27],
            [29, 29],
            [32, 32],
            [34, 34],
            [38, 38],
            [43, 43]
        ]
    }
)
solver.solve()
