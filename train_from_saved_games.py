from Games.ConnectFour.ConnectFour import ConnectFour
from Games.ConnectFour.ConnectFourNN import ResNet

import numpy as np
import os
import random
import shelve
from tqdm import trange
 
import torch
import torch.nn.functional as F

class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    


def train(args, model, optimizer, memory):
        
        random.shuffle(memory)
        
        for batch_start in range(0, len(memory), args["BATCH_SIZE"]):
            batch_end = batch_start + args["BATCH_SIZE"]    
                    
            training_memory = memory[batch_start : batch_end]

            state, action_prob, value = zip(*training_memory)

            state, action_prob, value =  np.array(state), np.array(action_prob), np.array(value).reshape(-1, 1)
            
            state = torch.tensor(state, device = model.device, dtype=torch.float32)
            policy_targets = torch.tensor(action_prob, device = model.device, dtype=torch.float32)
            value_targets = torch.tensor(value, device = model.device, dtype=torch.float32)
            
            out_policy, out_value = model(state)
            
            policy_loss = F.cross_entropy(out_policy, policy_targets)
            value_loss = F.mse_loss(out_value, value_targets)
            loss = policy_loss + value_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

def train_from_saved_data(args, model, optimizer, memory):
    try:
        model_path = os.path.join(args["MODEL_PATH"], 'model1.pt')
        optimizer_path = os.path.join(args["MODEL_PATH"], 'optimizer1.pt')

        model.load_state_dict(torch.load(model_path))
        optimizer.load_state_dict(torch.load(optimizer_path))
    except:
        print(Colors.RED + "UNABLE TO LOAD MODEL")
        print(Colors.GREEN + "SETTING UP NEW MODEL..." + Colors.RESET)
                
    else:
        print(Colors.GREEN + "MODEL FOUND\nLOADING MODEL..." + Colors.RESET)
    finally:
        print(Colors.YELLOW + "Training..." + Colors.RESET)
        model.train()
        for _ in trange(args["EPOCHS"]):
            train(args, model, optimizer, memory)
            
        print(Colors.YELLOW + "Saving Model...")
        torch.save(model.state_dict(), os.path.join(args["MODEL_PATH"], "model.pt"))
        torch.save(optimizer.state_dict(), os.path.join(args["MODEL_PATH"], "optimizer.pt"))
        print("Saved!" + Colors.RESET)


GAME = "ConnectFour" 

args = {
    "MODEL_PATH" : os.path.join(os.getcwd(), "Games", GAME, "models_n_optimizers"),

    "EXPLORATION_CONSTANT" : 2,

    "TEMPERATURE" : 1.25,

    "DIRICHLET_EPSILON" : 0.25,
    "DIRICHLET_ALPHA" : 0.3,
    "ROOT_RANDOMNESS": True,

    "ADVERSARIAL" : True,

    "NO_OF_SEARCHES" : 2000,
    "NO_ITERATIONS" : 200,
    "SELF_PLAY_ITERATIONS" : 100,
    "PARALLEL_PROCESS" : 100,
    "EPOCHS" : 6,
    "BATCH_SIZE" : 20,
    "MODEL_CHECK_GAMES" : 80,
    
}


game = ConnectFour()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device, "in use")

SAVE_GAME_PATH =  os.path.join(os.getcwd(), "Games", GAME, "games", "games_0.pkl")

with shelve.open(SAVE_GAME_PATH) as db:
    if "data" in db:
        memory = db["data"]

model = ResNet(game, 12, 124, device)
model.eval()

optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay = 0.0005)

train_from_saved_data(args, model, optimizer, memory)