import argparse
import torch
from torch.utils.data import DataLoader
from mosei_dataset import Mosei_Dataset
from model_bi import Model_bi
import random
from train import train, evaluate
import os

def parse_args():
    parser = argparse.ArgumentParser()
    # Model
    parser.add_argument('--model', type=str, default="Model_bi")#choices=["MCA", "JB", "GLIMPSE"])
    parser.add_argument('--layer', type=int, default=4)
    parser.add_argument('--hidden_size', type=int, default=512)
    parser.add_argument('--dropout_r', type=float, default=0.1)
    parser.add_argument('--multi_head', type=int, default=8)
    parser.add_argument('--ff_size', type=int, default=2048)
    parser.add_argument('--word_embed_size', type=int, default=300)
    parser.add_argument('--flat_mlp_size', type=int, default=512)
    parser.add_argument('--flat_glimpses', type=int, default=1)

    # Data
    parser.add_argument('--audio_seq_len', type=int, default=60)
    parser.add_argument('--lang_seq_len', type=int, default=60)
    parser.add_argument('--img_feat_size', type=int, default=1024)
    parser.add_argument('--audio_feat_size', type=int, default=1025)

    # Training
    parser.add_argument('--output', type=str, default='ckpt/')
    parser.add_argument('--name', type=str, default='exp0/')
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--max_epoch', type=int, default=99)
    parser.add_argument('--opt', type=str, default="Adam")
    parser.add_argument('--opt_params', type=str, default="{'betas': '(0.9, 0.98)', 'eps': '1e-9'}")
    parser.add_argument('--lr_base', type=float, default=0.00005)
    parser.add_argument('--lr_decay', type=float, default=0.5)
    parser.add_argument('--lr_decay_times', type=int, default=2)
    parser.add_argument('--warmup_epoch', type=float, default=0)
    parser.add_argument('--grad_norm_clip', type=float, default=-1)
    parser.add_argument('--eval_start', type=int, default=0)
    parser.add_argument('--early_stop', type=int, default=3)
    parser.add_argument('--seed', type=int, default=random.randint(0, 9999999))

    # Task
    parser.add_argument('--task', type=str, choices=['sentiment', 'emotion'], default='sentiment')
    parser.add_argument('--task_binary', type=bool, default=False)

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    print(args)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed(args.seed)
    torch.backends.cudnn.benchmark = True

    train_dset = Mosei_Dataset('train', args)
    eval_dset = Mosei_Dataset('valid', args, train_dset.token_to_ix)
    batch_size = args.batch_size

    net = eval(args.model)(args, train_dset.vocab_size, train_dset.pretrained_emb).cuda()
    print("Total number of parameters : " + str(sum([p.numel() for p in net.parameters()]) / 1e6) + "M")
    net = net.cuda()

    train_loader = DataLoader(train_dset, batch_size, shuffle=True, num_workers=8, pin_memory=True)
    eval_loader = DataLoader(eval_dset, batch_size, num_workers=8, pin_memory=True)

    if not os.path.exists(args.output + "/" + args.name):
        os.makedirs(args.output + "/" + args.name)

    eval_accuracies = train(net, train_loader, eval_loader, args)

    # #testing
    # test_dset = Mosei_Dataset('test', args, train_dset.token_to_ix)
    # test_loader = DataLoader(test_dset, batch_size, num_workers=8, pin_memory=True)
    #
    # state_dict = torch.load(args.output + "/" + args.name +
    #                         '/best' + str(max(eval_accuracies)) + "_" + str(args.seed)+'.pkl')['state_dict']
    # net.load_state_dict(state_dict)
    #
    # test_accuracy, _ = evaluate(net, test_loader)
    # print("Test accuracy:", test_accuracy)
    # with open("best_scores", "a+") as f:
    #     f.write(args.output + "/" + args.name + ","
    #             + str(test_accuracy) + "("
    #             + str(max(eval_accuracies))+") | ("
    #             + str(eval_accuracies) + ")\n")