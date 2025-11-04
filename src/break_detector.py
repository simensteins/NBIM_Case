def detect_breaks(events):

    # Simple break detection based on NET_AMOUNT_SC difference

    breaks = []

    for event in events:

        nbim_net_sc = event['nbim_rows']['NET_AMOUNT_SC']
        custody_net_sc = event['custody_rows']['NET_AMOUNT_SC']

        diff = abs(nbim_net_sc - custody_net_sc)
        event['NET_AMOUNT_SC_DIFF'] = diff
        
        if diff > 0:
            breaks.append(event)

    return breaks


