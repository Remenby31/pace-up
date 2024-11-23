import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from Model import LSTMModel
import glob
import os

def preprocess_data(file_paths, seq_length):
    """
    Preprocess multiple datasets and combine them
    """
    all_sequences = []
    all_targets = []
    
    # Initialize scaler
    scaler = MinMaxScaler()
    
    # First pass: fit scaler on all data
    all_data = []
    for file_path in file_paths:
        df = pd.read_csv(file_path, parse_dates=['timestamp'])
        df.set_index('timestamp', inplace=True)
        all_data.append(df.values)
    
    # Fit scaler on combined data
    combined_data = np.vstack(all_data)
    scaler.fit(combined_data)
    
    # Second pass: create sequences for each dataset
    for file_path in file_paths:
        df = pd.read_csv(file_path, parse_dates=['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Transform data using the fitted scaler
        scaled_data = scaler.transform(df)
        
        # Create sequences
        for i in range(len(scaled_data) - seq_length):
            seq = scaled_data[i:i + seq_length]
            target = scaled_data[i + seq_length]
            all_sequences.append(seq)
            all_targets.append(target)
    
    return np.array(all_sequences), np.array(all_targets), scaler

def load_datasets(data_dir):
    """
    Load all dataset files from the specified directory
    """
    file_pattern = os.path.join(data_dir, "activity_data_*.csv")
    files = glob.glob(file_pattern)
    if not files:
        raise ValueError(f"No data files found matching pattern: {file_pattern}")
    print(f"Found {len(files)} dataset files: {[os.path.basename(f) for f in files]}")
    return sorted(files)

def train_model(model, X_train, y_train, criterion, optimizer, epochs, batch_size=32):
    """
    Train the model using batches
    """
    n_samples = len(X_train)
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        n_batches = 0
        
        # Create random indices for shuffling
        indices = torch.randperm(n_samples)
        
        # Process data in batches
        for start_idx in range(0, n_samples, batch_size):
            batch_indices = indices[start_idx:start_idx + batch_size]
            
            X_batch = X_train[batch_indices]
            y_batch = y_train[batch_indices]
            
            optimizer.zero_grad()
            output = model(X_batch)
            loss = criterion(output, y_batch)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
        
        avg_loss = total_loss / n_batches
        if (epoch + 1) % 10 == 0:  # Print every 10 epochs
            print(f"Epoch [{epoch+1}/{epochs}], Average Loss: {avg_loss:.4f}")

def validate_model(model, X_test, y_test, criterion):
    """
    Validate the model and return validation loss
    """
    model.eval()
    with torch.no_grad():
        output = model(X_test)
        val_loss = criterion(output, y_test)
    return val_loss.item()

def main():
    # Hyperparameters
    SEQ_LENGTH = 60
    INPUT_DIM = 3  # pace_min_per_km, elevation_meters, heart_rate_bpm
    HIDDEN_DIM = 50
    OUTPUT_DIM = 3
    NUM_LAYERS = 2
    EPOCHS = 100
    LR = 0.001
    BATCH_SIZE = 32
    
    # Load all datasets
    try:
        file_paths = load_datasets("average_data")
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Prepare data
    sequences, targets, scaler = preprocess_data(file_paths, SEQ_LENGTH)
    X_train, X_test, y_train, y_test = train_test_split(
        sequences, targets, test_size=0.2, random_state=42
    )
    
    # Convert to tensors
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32)
    
    # Initialize model, loss, and optimizer
    model = LSTMModel(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM, NUM_LAYERS)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    
    # Train the model
    print("Starting training...")
    train_model(model, X_train, y_train, criterion, optimizer, EPOCHS, BATCH_SIZE)
    
    # Validate the model
    val_loss = validate_model(model, X_test, y_test, criterion)
    print(f"Final validation loss: {val_loss:.4f}")
    
    # Save the model and scaler
    torch.save({
        'model_state_dict': model.state_dict(),
        'scaler': scaler,
        'hyperparameters': {
            'seq_length': SEQ_LENGTH,
            'input_dim': INPUT_DIM,
            'hidden_dim': HIDDEN_DIM,
            'output_dim': OUTPUT_DIM,
            'num_layers': NUM_LAYERS
        }
    }, "lstm_model.pth")
    print("Model and scaler saved as lstm_model.pth")

if __name__ == "__main__":
    main()