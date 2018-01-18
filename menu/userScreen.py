import parameters as param
import graphics as graph
import menu


class UserScreen(menu.Menu):
    def __init__(self):

        self.users = users = ["New user", 'Blank line'] + param.get_users()
        menu.Menu.__init__(self, options=users,
                           # actions=dict([(user, choose_user) for user in users]),
                           title="Please select your user profile",
                           choose_once=True,
                           default=users.index(param.USER))

    def save(self):
        self.select()  # Enter should choose a user too
        menu.Menu.save(self)

    def choose(self, k, i):
        newuser = self.users[i]
        if newuser == "New user":
            graph.TextInputScreen("Enter new user name:", param.USER, callback=param.set_user, catch=' ')
        else:
            param.set_user(newuser)
